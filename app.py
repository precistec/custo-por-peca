import streamlit as st
import pandas as pd

st.set_page_config(page_title="Custo por Peça", layout="centered")

st.title("🔧 Cálculo de Custo por Peça")

st.write("Faça o upload da Requisição e da Nota Fiscal")

req_file = st.file_uploader("📄 Requisição", type=["xlsx", "xls", "pdf"])
nf_file = st.file_uploader("🧾 Nota Fiscal", type=["xlsx", "xls", "pdf", "xml"])

if req_file and nf_file:
    st.success("Arquivos carregados com sucesso!")
    st.write("Próximo passo: processar os dados.")
