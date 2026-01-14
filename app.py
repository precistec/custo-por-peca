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
    # 1. LER MATÉRIA-PRIMA DA NF
    # =============================
    nf_mp = defaultdict(float)

    for linha in linhas_nf:
        linha = linha.replace(".", "").strip()

        # Linha começa com código numérico
        if re.match(r"^\d{2,5}\s", linha):
            valores = re.findall(r"\d+,\d+", linha)

            if len(valores) >= 3:
                codigo = linha.split()[0]
                valor_total = float(valores[-1].replace(",", "."))
                nf_mp[codigo] += valor_total

    # =============================
    # 2. LER REQUISIÇÃO
    # =============================
    itens = []
    i = 0

    while i < len(linhas_req) - 2:
        prod = linhas_req[i]
        qtd = linhas_req[i + 1]
        mp = linhas_req[i + 2]

        if "PRODUTO INTERMEDIÁRIO" in prod and "MATÉRIA-PRIMA" in mp:
            cod_prod = re.findall(r"\b\d{4,5}\b", prod)
            cod_mp = re.findall(r"\b\d{2,5}\b", mp)
            qtd_prod = re.findall(r"\b\d+\b", qtd)

            if cod_prod and cod_mp and qtd_prod:
                itens.append({
                    "produto": cod_prod[0],
                    "mp": cod_mp[0],
                    "qtd": int(qtd_prod[0]),
                    "linha_mp": mp
                })
                i += 3
            else:
                i += 1
        else:
            i += 1

    # =============================
    # 3. CÁLCULO FINAL (SIMPLES)
    # =============================
    resultado = []

    for item in itens:
        produto = item["produto"]
        mp = item["mp"]
        qtd = item["qtd"]
        linha_mp = item["linha_mp"]

        if "ALMOXARIFADO" in linha_mp.upper():
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

    st.success("Processamento concluído corretamente")
    st.dataframe(df)

    st.download_button(
        "⬇️ Baixar CSV",
        df.to_csv(index=False, sep=";").encode("utf-8"),
        "custo_por_peca.csv",
        "text/csv",
        key="download_unico"
    )
