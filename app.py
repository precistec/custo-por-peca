import streamlit as st
import pandas as pd
import pdfplumber

st.set_page_config(page_title="Custo por Peça", layout="centered")

st.title("🔧 Cálculo de Custo por Peça")
st.write("Upload da Requisição e da Nota Fiscal")

req_file = st.file_uploader("📄 Requisição (PDF ou Excel)", type=["xlsx", "xls", "pdf"])
nf_file = st.file_uploader("🧾 Nota Fiscal (PDF ou XML)", type=["xlsx", "xls", "pdf", "xml"])

def ler_requisicao_excel(file):
    df = pd.read_excel(file)
    return df

def ler_requisicao_pdf(file):
    linhas = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            texto = page.extract_text()
            if texto:
                for linha in texto.split("\n"):
                    linhas.append(linha)
    return linhas

if req_file and nf_file:
    st.success("Arquivos carregados com sucesso!")

    if st.button("▶️ Processar dados"):
        st.info("Lendo requisição...")

        if req_file.name.endswith(".pdf"):
            dados_req = ler_requisicao_pdf(req_file)
            st.subheader("📄 Linhas extraídas da Requisição (PDF)")
            st.write(dados_req[:20])  # mostra só as primeiras linhas

        else:
            df_req = ler_requisicao_excel(req_file)
            st.subheader("📊 Requisição (Excel)")
            st.dataframe(df_req)
