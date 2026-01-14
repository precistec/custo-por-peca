import streamlit as st
import pandas as pd

st.set_page_config(page_title="Custo por Peça", layout="centered")

st.title("🔧 Cálculo de Custo por Peça")
st.write("Faça o upload da Requisição e da Nota Fiscal")

req_file = st.file_uploader("📄 Requisição", type=["xlsx", "xls", "pdf"])
nf_file = st.file_uploader("🧾 Nota Fiscal", type=["xlsx", "xls", "pdf", "xml"])

if req_file and nf_file:
    st.success("Arquivos carregados com sucesso!")

    if st.button("▶️ Processar dados"):
        st.info("Processando...")

        # Resultado de teste (mock)
        dados = [
            {"Código Produto": "23498", "Preço por Peça": 104.92},
            {"Código Produto": "23648", "Preço por Peça": 0.53},
            {"Código Produto": "23649", "Preço por Peça": 35.88},
        ]

        df = pd.DataFrame(dados)

        st.subheader("📊 Resultado")
        st.dataframe(df, use_container_width=True)

        st.success("Processamento concluído!")
