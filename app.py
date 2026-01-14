import streamlit as st
import tabula
import pandas as pd
import re
from collections import defaultdict

st.set_page_config(page_title="Custo por Peça (PDF)", layout="centered")
st.title("Cálculo de Custo por Peça a partir de PDFs")

nf_file = st.file_uploader("📄 Nota Fiscal (PDF)", type="pdf")
req_file = st.file_uploader("📄 Requisição (PDF)", type="pdf")

if st.button("🔧 Processar"):

    if not nf_file or not req_file:
        st.error("Envie a Nota Fiscal e a Requisição.")
        st.stop()

    # ======================================
    # 1. EXTRAIR TABELAS DA NOTA FISCAL
    # ======================================
    st.info("Extraindo tabela da Nota Fiscal (isso pode demorar alguns segundos)...")
    try:
        # Retorna uma lista de DataFrames (uma tabela por página)
        tabelas_nf = tabula.read_pdf(nf_file, pages="all", lattice=True)
    except Exception as e:
        st.error(f"Erro ao ler NF: {e}")
        st.stop()

    nf_mp = defaultdict(float)

    for tabela in tabelas_nf:
        tabela = tabela.fillna("")
        for idx, row in tabela.iterrows():
            # Tenta pegar código e valor total
            try:
                codigo = str(row[0]).strip()
                valor = str(row[-1]).replace(".", "").replace(",", ".").strip()
                if codigo.isdigit() and valor:
                    nf_mp[codigo] += float(valor)
            except:
                continue

    st.subheader("DEBUG – Matérias-primas capturadas da NF")
    st.write(dict(nf_mp))

    # ======================================
    # 2. EXTRAIR TABELA DA REQUISIÇÃO
    # ======================================
    st.info("Extraindo tabela da Requisição...")
    try:
        tabelas_req = tabula.read_pdf(req_file, pages="all", lattice=True)
    except Exception as e:
        st.error(f"Erro ao ler Requisição: {e}")
        st.stop()

    itens = []

    for tabela in tabelas_req:
        tabela = tabela.fillna("")
        for i in range(len(tabela) - 2):
            linha_prod = str(tabela.iloc[i,0])
            linha_qtd = str(tabela.iloc[i+1,0])
            linha_mp = str(tabela.iloc[i+2,0])

            if "PRODUTO INTERMEDIÁRIO" in linha_prod and "MATÉRIA-PRIMA" in linha_mp:
                cod_prod = re.findall(r"\b\d{4,5}\b", linha_prod)
                cod_mp = re.findall(r"\b\d{2,5}\b", linha_mp)
                qtd = re.findall(r"\b\d+\b", linha_qtd)

                if cod_prod and cod_mp and qtd:
                    itens.append({
                        "produto": cod_prod[0],
                        "mp": cod_mp[0],
                        "qtd": int(qtd[0]),
                        "linha_mp": linha_mp.upper()
                    })

    # ======================================
    # 3. CALCULO PREÇO POR PEÇA
    # ======================================
    resultado = []

    for item in itens:
        produto = item["produto"]
        mp = item["mp"]
        qtd = item["qtd"]
        linha_mp = item["linha_mp"]

        if "ALMOXARIFADO" in linha_mp:
            preco = "ALMOXARIFADO"
        elif mp not in nf_mp:
            preco = "Não consta na NF"
        else:
            preco = round(nf_mp[mp] / qtd, 4)

        resultado.append({
            "Código do Produto": produto,
            "Preço por Peça": preco
        })

    df = pd.DataFrame(resultado)
    st.subheader("Resultado Final")
    st.dataframe(df)

    st.download_button(
        "⬇️ Baixar CSV",
        df.to_csv(index=False, sep=";").encode("utf-8"),
        "custo_por_peca.csv",
        "text/csv"
    )
