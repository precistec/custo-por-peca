import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Precistec - Custo por Peça", layout="wide")

st.title("Precistec – Conferência de Custo por Peça")

st.markdown("""
Cole **a Nota Fiscal** e **a Requisição** nos campos abaixo.  
O sistema irá cruzar os dados seguindo o **procedimento definitivo da Precistec**.
""")

col1, col2 = st.columns(2)

with col1:
    nf_texto = st.text_area("📄 Nota Fiscal (cole exatamente como vem)", height=300)

with col2:
    req_texto = st.text_area("📋 Requisição (cole exatamente como vem)", height=300)

processar = st.button("🔍 Processar NF x Requisição")

# =========================
# FUNÇÕES DE LEITURA
# =========================

def ler_nf(texto):
    linhas = texto.splitlines()
    dados = []

    for linha in linhas:
        partes = re.split(r"\s{2,}", linha.strip())
        if len(partes) >= 9 and partes[0].isdigit():
            try:
                dados.append({
                    "CODIGO_MP": partes[0],
                    "DESCRICAO_MP": partes[1],
                    "UNIDADE": partes[5],
                    "QUANTIDADE_NF": float(partes[6].replace(",", ".")),
                    "VALOR_TOTAL_NF": float(partes[8].replace(".", "").replace(",", "."))
                })
            except:
                pass

    return pd.DataFrame(dados)

def ler_requisicao(texto):
    linhas = texto.splitlines()
    dados = []
    produto_atual = None

    for linha in linhas:
        if "PRODUTO INTERMEDIÁRIO" in linha:
            partes = linha.split()
            produto_atual = {
                "CODIGO_PRODUTO": partes[-2],
                "DESCRICAO_PRODUTO": " ".join(partes[3:-2]),
                "QTDE_PECAS": int(partes[-1])
            }

        elif "MATÉRIA-PRIMA" in linha and produto_atual:
            partes = linha.split()
            dados.append({
                **produto_atual,
                "CODIGO_MP": partes[-2],
                "QTDE_REQUISICAO": float(partes[-1].replace(",", "."))
            })
            produto_atual = None

    return pd.DataFrame(dados)

# =========================
# PROCESSAMENTO
# =========================

if processar:
    if not nf_texto or not req_texto:
        st.error("Cole a Nota Fiscal e a Requisição.")
    else:
        df_nf = ler_nf(nf_texto)
        df_req = ler_requisicao(req_texto)

        st.subheader("📄 Nota Fiscal – Dados lidos")
        st.dataframe(df_nf)

        st.subheader("📋 Requisição – Dados lidos")
        st.dataframe(df_req)

        st.success("Leitura concluída. Próximo passo: cálculo e rateio definitivo.")
