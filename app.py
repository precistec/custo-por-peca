import streamlit as st
import pandas as pd
import pdfplumber
import re

st.set_page_config(page_title="Custo por Peça", layout="centered")

st.title("🔧 Cálculo de Custo por Peça")

req_file = st.file_uploader("📄 Requisição (PDF ou Excel)", type=["xlsx", "xls", "pdf"])
nf_file = st.file_uploader("🧾 Nota Fiscal (PDF ou XML)", type=["xlsx", "xls", "pdf", "xml"])

def limpar_linhas(linhas):
    limpas = []
    for l in linhas:
        if re.search(r"\d{4,}", l):
            limpas.append(l)
    return limpas

def ler_requisicao_pdf(file):
    linhas = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            texto = page.extract_text()
            if texto:
                linhas.extend(texto.split("\n"))
    return limpar_linhas(linhas)

def ler_nf_pdf(file):
    materias = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            texto = page.extract_text()
            if texto:
                for linha in texto.split("\n"):
                    if re.search(r"\d{4,}.*\d+,\d{2}", linha):
                        materias.append(linha)
    return materias

if req_file and nf_file:
    st.success("Arquivos carregados!")

    if st.button("▶️ Processar"):
        st.subheader("📄 REQUISIÇÃO")
        if req_file.name.endswith(".pdf"):
            linhas = ler_requisicao_pdf(req_file)
            for i in range(0, len(linhas) - 1, 2):
                st.write("Produto:", linhas[i])
                st.write("MP:", linhas[i + 1])
                st.markdown("---")
        else:
            df = pd.read_excel(req_file)
            st.dataframe(df)

        st.subheader("🧾 NOTA FISCAL (Matéria-Prima)")
        if nf_file.name.endswith(".pdf"):
            materias = ler_nf_pdf(nf_file)
            for m in materias:
                st.write(m)
