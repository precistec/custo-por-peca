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
    # 1. EXTRAIR MATÉRIA-PRIMA DA NF
    # =============================
    nf_mp = defaultdict(float)

    for linha in linhas_nf:
        linha = linha.strip()

        # Linha começa com código numérico
        if re.match(r"^\d{2,5}\s", linha):
            valores = re.findall(r"\d+,\d+", linha)

            if len(valores) >= 3:
                codigo = linha.split()[0]
                valor_total = float(valores[-1].replace(",", "."))
                nf_mp[codigo] += valor_total

    # =============================
    # 2. EXTRAIR REQUISIÇÃO
    # =============================
    itens = []
    i = 0

    while i < len(linhas_req) - 2:
        linha_prod = linhas_req[i]
        linha_qtd = linhas_req[i + 1]
        linha_mp = linhas_req[i + 2]

        if "PRODUTO INTERMEDIÁRIO" in linha_prod and "MATÉRIA-PRIMA" in linha_mp:

            prod_codigo = re.findall(r"\b\d{4,5}\b", linha_prod)
            mp_codigo = re.findall(r"\b\d{2,5}\b", linha_mp)
            qtd = re.findall(r"\b\d+\b", linha_qtd)

            if prod_codigo and mp_codigo and qtd:
                itens.append({
                    "produto": prod_codigo[0],
                    "mp": mp_codigo[0],
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

    # =============================
    # 4. SAÍDA
    # =============================
    df = pd.DataFrame(resultado)

    st.success("Processamento concluído com sucesso")
    st.dataframe(df)

    st.download_button(
        label="⬇️ Baixar CSV",
        data=df.to_csv(index=False, sep=";").encode("utf-8"),
        file_name="custo_por_peca.csv",
        mime="text/csv",
        key="download_csv_unico"
    )
