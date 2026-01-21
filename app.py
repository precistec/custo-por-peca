import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Cálculo de Custo por Peça", layout="wide")

st.title("Cálculo de Custo por Peça - Precistec")

# Campos de texto para colar Requisição e Nota Fiscal
req_text = st.text_area("Cole a Requisição aqui", height=300)
nf_text = st.text_area("Cole a Nota Fiscal aqui", height=300)

def parse_requisicao(texto):
    produtos = []
    linhas = texto.strip().splitlines()
    i = 0
    while i < len(linhas):
        linha = linhas[i].strip()
        # Produto intermediário
        match_prod = re.match(r'PRODUTO INTERMEDIÁRIO.*?\)? (\d+)\s+(.+?)\s+(\d+)$', linha)
        if match_prod:
            codigo_prod, descricao_prod, qtde_prod = match_prod.groups()
            qtde_prod = int(qtde_prod)
            # próxima linha deve ser matéria-prima
            i += 1
            if i < len(linhas):
                linha_mp = linhas[i].strip()
                match_mp = re.match(r'MATÉRIA-PRIMA.*?\)? (\d+)\s+(.+?)\s+([\d.,]+)$', linha_mp)
                if match_mp:
                    codigo_mp, descricao_mp, qtde_mp = match_mp.groups()
                    qtde_mp = float(qtde_mp.replace(",", "."))
                    produtos.append({
                        "produto_codigo": codigo_prod,
                        "produto_descricao": descricao_prod,
                        "produto_qtde": qtde_prod,
                        "mp_codigo": codigo_mp,
                        "mp_descricao": descricao_mp,
                        "mp_qtde": qtde_mp
                    })
        i += 1
    return pd.DataFrame(produtos)

def parse_nf(texto):
    nf_itens = []
    linhas = texto.strip().splitlines()
    for linha in linhas:
        linha = linha.strip()
        match_nf = re.match(
            r'(\d+)\s+(.+?)\s+\d{8,10}\s+\d{3}\s+\d{4}\s+(\w+)\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+).*', 
            linha
        )
        if match_nf:
            codigo, descricao, unidade, qtde, vunit, vtotal = match_nf.groups()
            qtde = float(qtde.replace(",", "."))
            vunit = float(vunit.replace(",", "."))
            vtotal = float(vtotal.replace(",", "."))
            nf_itens.append({
                "mp_codigo": codigo,
                "mp_descricao": descricao,
                "unidade": unidade,
                "qtde_nf": qtde,
                "vunit_nf": vunit,
                "vtotal_nf": vtotal
            })
    return pd.DataFrame(nf_itens)

def calcular_precos(df_req, df_nf):
    resultados = []
    for idx, row in df_req.iterrows():
        mp_nf = df_nf[df_nf["mp_codigo"] == row["mp_codigo"]]
        if mp_nf.empty:
            resultados.append({
                "produto_codigo": row["produto_codigo"],
                "produto_descricao": row["produto_descricao"],
                "produto_qtde": row["produto_qtde"],
                "preco_peca": "Não consta na NF",
                "total": "Não consta na NF",
                "divergencia": "MP não consta na NF"
            })
        else:
            # Se quantidade da NF diferente da requisição, ratear pelo total da NF
            vtotal_nf = mp_nf["vtotal_nf"].sum()
            qtde_total_req = df_req[df_req["mp_codigo"] == row["mp_codigo"]]["produto_qtde"].sum()
            preco_peca = vtotal_nf / qtde_total_req
            total = preco_peca * row["produto_qtde"]
            resultados.append({
                "produto_codigo": row["produto_codigo"],
                "produto_descricao": row["produto_descricao"],
                "produto_qtde": row["produto_qtde"],
                "preco_peca": round(preco_peca, 4),
                "total": round(total, 2),
                "divergencia": "" if vtotal_nf > 0 else "Quantidade MP NF ≠ requisição"
            })
    return pd.DataFrame(resultados)

# Processar
if req_text and nf_text:
    try:
        df_req = parse_requisicao(req_text)
        df_nf = parse_nf(nf_text)

        if df_req.empty:
            st.error("Não foi possível interpretar a requisição. Verifique o texto colado.")
        elif df_nf.empty:
            st.error("Não foi possível interpretar a Nota Fiscal. Verifique o texto colado.")
        else:
            df_result = calcular_precos(df_req, df_nf)
            st.subheader("Resultado por Produto")
            st.dataframe(df_result)

            # Soma total
            soma_total = df_result[df_result["total"].apply(lambda x: isinstance(x, (int,float)))].total.sum()
            st.write(f"💰 Total geral (excluindo itens não existentes na NF): R$ {soma_total:.2f}")
    except Exception as e:
        st.error(f"❌ Erro ao processar: {e}")
else:
    st.info("Cole a Requisição e a Nota Fiscal nos campos acima e clique fora para processar.")
