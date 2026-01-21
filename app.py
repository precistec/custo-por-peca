import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Cálculo de Custo por Peça - Precistec", layout="wide")

st.title("Precistec - Cálculo de Custo por Peça")
st.markdown("Cole a Requisição e a Nota Fiscal nos campos abaixo:")

# Campos de texto
req_text = st.text_area("Requisição", height=300)
nf_text = st.text_area("Nota Fiscal", height=300)

# Função para limpar strings e converter números
def parse_float(text):
    try:
        return float(text.replace(",", "."))
    except:
        return None

# Função para processar Requisição
def parse_requisicao(texto):
    linhas = texto.strip().split("\n")
    itens = []
    produto = None
    for l in linhas:
        l = l.strip()
        if l.startswith("PRODUTO INTERMEDIÁRIO"):
            m = re.match(r"PRODUTO INTERMEDIÁRIO.*?(\d+)\s+(.*)\s+(\d+)$", l)
            if m:
                produto = {
                    "codigo_prod": m.group(1),
                    "descricao_prod": m.group(2),
                    "qtde_prod": int(m.group(3)),
                    "mp_codigo": None,
                    "mp_descricao": None,
                    "mp_consumo": None
                }
        elif l.startswith("MATÉRIA-PRIMA"):
            m = re.match(r"MATÉRIA-PRIMA.*?(\d+)\s+(.*)\s+([\d\.]+)$", l)
            if m and produto:
                produto["mp_codigo"] = m.group(1)
                produto["mp_descricao"] = m.group(2)
                produto["mp_consumo"] = parse_float(m.group(3))
                itens.append(produto)
                produto = None
    return pd.DataFrame(itens)

# Função para processar NF
def parse_nf(texto):
    linhas = texto.strip().split("\n")
    nf_itens = []
    for l in linhas[1:]:
        partes = re.split(r"\s{2,}", l.strip())
        if len(partes) >= 11:
            qtde = parse_float(partes[6])
            valor_total = parse_float(partes[8])
            nf_itens.append({
                "mp_codigo": partes[0],
                "mp_descricao": partes[1].replace('"','').strip(),
                "qtde_nf": qtde,
                "valor_total_nf": valor_total,
                "uni": partes[4]
            })
    return pd.DataFrame(nf_itens)

# Função para calcular preço por peça
def calcular_custo(req_df, nf_df):
    res = []
    for idx, row in req_df.iterrows():
        mp_nf = nf_df[nf_df["mp_codigo"]==row["mp_codigo"]]
        preco_peca = None
        total = None
        divergencia = ""
        if mp_nf.empty:
            preco_peca = "Não consta na NF"
            total = "Não consta na NF"
            divergencia = "MP não consta na NF"
        else:
            # rateio proporcional se houver diferença de quantidade
            valor_total_nf = mp_nf["valor_total_nf"].sum()
            total_consumo_nf = mp_nf["qtde_nf"].sum()
            consumo_req = row["mp_consumo"] * row["qtde_prod"]
            if total_consumo_nf != consumo_req:
                preco_peca = round(valor_total_nf / row["qtde_prod"],2)
                total = round(preco_peca * row["qtde_prod"],2)
                divergencia = "Quantidade MP NF ≠ requisição"
            else:
                preco_peca = round(valor_total_nf / row["qtde_prod"],2)
                total = round(preco_peca * row["qtde_prod"],2)
        res.append({
            "CÓDIGO": row["codigo_prod"],
            "DESCRIÇÃO": row["descricao_prod"],
            "QTDE": row["qtde_prod"],
            "R$/PEÇA": preco_peca,
            "TOTAL (R$)": total,
            "DIVERGÊNCIA": divergencia
        })
    return pd.DataFrame(res)

if st.button("Gerar Planilha"):
    try:
        req_df = parse_requisicao(req_text)
        nf_df = parse_nf(nf_text)

        if req_df.empty or nf_df.empty:
            st.error("❌ Não foi possível interpretar a requisição ou a NF. Verifique o texto colado.")
        else:
            df_final = calcular_custo(req_df, nf_df)
            st.success("✅ Planilha gerada com sucesso!")
            st.dataframe(df_final)
            
            # Mostrar total geral
            total_geral = df_final[df_final["TOTAL (R$)"].apply(lambda x: isinstance(x,float))]["TOTAL (R$)"].sum()
            st.write(f"**TOTAL GERAL (NF): R$ {total_geral:.2f}**")
    except Exception as e:
        st.error(f"Erro ao processar: {e}")
