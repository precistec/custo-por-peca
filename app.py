import streamlit as st
import pdfplumber
import pandas as pd
import re
from collections import defaultdict

st.set_page_config(page_title="Custo por Peça", layout="centered")
st.title("Cálculo de Custo por Peça")

nf_file = st.file_uploader("📄 Nota Fiscal (PDF)", type="pdf")
req_file = st.file_uploader("📄 Requisição (PDF)", type="pdf")

def extrair_linhas(pdf):
    linhas = []
    with pdfplumber.open(pdf) as p:
        for page in p.pages:
            texto = page.extract_text()
            if texto:
                linhas.extend(texto.split("\n"))
    return linhas

if st.button("🔧 Processar"):

    if not nf_file or not req_file:
        st.error("Envie a Nota Fiscal e a Requisição.")
        st.stop()

    linhas_nf = extrair_linhas(nf_file)
    linhas_req = extrair_linhas(req_file)

    # =============================
    # 1. LER NOTA FISCAL (MP)
    # =============================
    nf_mp = defaultdict(float)

    for linha in linhas_nf:
        linha = linha.strip()

        # Linha começa com código numérico
        if re.match(r"^\d{2,5}\s", linha):
            valores = re.findall(r"\d+,\d+", linha)

            if valores:
                codigo_mp = linha.split()[0]
                valor_total = float(valores[-1].replace(",", "."))
                nf_mp[codigo_mp] += valor_total

    # =============================
    # 2. LER REQUISIÇÃO
    # =============================
    itens = []
    i = 0

    while i < len(linhas_req) - 2:
        linha_prod = linhas_req[i]
        linha_qtd = linhas_req[i + 1]
        linha_mp = linhas_req[i + 2]

        if "PRODUTO INTERMEDIÁRIO" in linha_prod and "MATÉRIA-PRIMA" in linha_mp:
            cod_prod = re.findall(r"\b\d{4,5}\b", linha_prod)
            cod_mp = re.findall(r"\b\d{2,5}\b", linha_mp)
            qtd = re.findall(r"\b\d+\b", linha_qtd)

            if cod_prod and cod_mp and qtd:
                itens.append({
                    "produto": cod_prod[0],
                    "mp": cod_mp[0],
                    "qtd": int(qtd[0]),
                    "linha_mp": linha_mp
                })
                i += 3
            else:
                i += 1
        else:
            i += 1

    # =============================
    # 3. CÁLCULO FINAL
    # =============================
    resultado = []

    for item in itens:
        produto = item["produto"]
        mp = item["mp"]
        qtd = item["qtd"]
        linha_mp = item["linha_mp"].upper()

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

    st.success("Processamento concluído")
    st.dataframe(df)

    st.download_button(
        label="⬇️ Baixar CSV",
        data=df.to_csv(index=False, sep=";").encode("utf-8"),
        file_name="custo_por_peca.csv",
        mime="text/csv",
        key="download_custo"
    )
