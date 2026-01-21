import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Custo por Peça - Precistec", layout="wide")
st.title("Cálculo de Custo por Peça - Precistec")

# --- INPUT TEXT AREA ---
st.subheader("Cole a Requisição")
req_text = st.text_area("Requisição", height=300)

st.subheader("Cole a Nota Fiscal")
nf_text = st.text_area("Nota Fiscal", height=300)

# --- FUNÇÕES ---
def parse_requisicao(texto):
    """
    Converte o texto da requisição em DataFrame estruturado
    """
    linhas = [l.strip() for l in texto.split("\n") if l.strip()]
    produtos = []
    i = 0
    while i < len(linhas):
        linha = linhas[i]
        if linha.startswith("PRODUTO INTERMEDIÁRIO"):
            partes = linha.split()
            codigo = partes[2]
            quantidade = partes[-1].replace(",", ".")
            descricao = " ".join(partes[3:-1])
            produtos.append({
                "tipo": "P",
                "codigo_prod": codigo,
                "descricao_prod": descricao,
                "qtde_prod": float(quantidade),
                "codigo_mp": None,
                "descricao_mp": None,
                "qtde_mp": None
            })
            i += 1
            if i < len(linhas) and linhas[i].startswith("MATÉRIA-PRIMA"):
                linha_mp = linhas[i]
                partes_mp = linha_mp.split()
                codigo_mp = partes_mp[2]
                quantidade_mp = partes_mp[-1].replace(",", ".")
                descricao_mp = " ".join(partes_mp[3:-1])
                produtos[-1]["codigo_mp"] = codigo_mp
                produtos[-1]["descricao_mp"] = descricao_mp
                produtos[-1]["qtde_mp"] = float(quantidade_mp)
        i += 1
    df = pd.DataFrame(produtos)
    return df

def parse_nf(texto):
    """
    Converte o texto da NF em DataFrame estruturado
    """
    linhas = [l.strip() for l in texto.split("\n") if l.strip()]
    nf_itens = []
    for linha in linhas[1:]:  # pular header
        # separar por regex múltiplos espaços
        partes = re.split(r'\s{2,}', linha)
        if len(partes) < 6:
            continue
        codigo = partes[0]
        descricao = partes[1]
        qtde = partes[7].replace(",", ".") if len(partes) > 7 else "0"
        valor_total = partes[9].replace(",", ".") if len(partes) > 9 else "0"
        unidade = partes[6]
        nf_itens.append({
            "codigo_mp": codigo,
            "descricao_mp": descricao,
            "qtde_nf": float(qtde),
            "valor_total": float(valor_total),
            "unidade": unidade
        })
    df = pd.DataFrame(nf_itens)
    return df

def calcular_preco(df_req, df_nf):
    """
    Calcula preço por peça e identifica divergências
    """
    precos = []
    for idx, row in df_req.iterrows():
        codigo_mp = row["codigo_mp"]
        qtde_prod = row["qtde_prod"]
        qtde_mp_req = row["qtde_mp"]
        
        nf_item = df_nf[df_nf["codigo_mp"] == codigo_mp]
        if nf_item.empty:
            preco_peca = "Não consta na NF"
            total = "Não consta na NF"
            divergencia = "MP não consta na NF"
        else:
            valor_total_nf = nf_item["valor_total"].sum()
            qtde_nf = nf_item["qtde_nf"].sum()
            if qtde_nf != qtde_mp_req:
                # usar valor total da NF dividido pela quantidade da requisição
                preco_peca = round(valor_total_nf / qtde_prod, 4)
                total = round(preco_peca * qtde_prod, 2)
                divergencia = "Quantidade MP NF ≠ requisição"
            else:
                preco_peca = round(valor_total_nf / qtde_prod, 4)
                total = round(preco_peca * qtde_prod, 2)
                divergencia = "-"
        precos.append({
            "codigo_prod": row["codigo_prod"],
            "descricao_prod": row["descricao_prod"],
            "qtde_prod": qtde_prod,
            "preco_peca": preco_peca,
            "total": total,
            "divergencia": divergencia
        })
    return pd.DataFrame(precos)

# --- EXECUÇÃO ---
if st.button("Processar"):
    try:
        df_req = parse_requisicao(req_text)
        df_nf = parse_nf(nf_text)
        if df_req.empty or df_nf.empty:
            st.error("❌ Não foi possível interpretar a requisição ou a NF. Verifique o texto colado.")
        else:
            df_result = calcular_preco(df_req, df_nf)
            st.subheader("Tabela de Preço por Peça")
            st.dataframe(df_result)
            st.markdown(f"**Total Geral (somando coluna 'total')**: R$ {df_result[df_result['total'] != 'Não consta na NF']['total'].sum():,.2f}")
    except Exception as e:
        st.error(f"Erro ao processar: {e}")
