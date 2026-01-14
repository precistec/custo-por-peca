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
        st.error("Envie os dois arquivos.")
        st.stop()

    linhas_nf = extrair_linhas(nf_file)
    linhas_req = extrair_linhas(req_file)

    # =============================
    # 1. NOTA FISCAL – MATÉRIA-PRIMA
    # =============================
    nf_mp = {}

    for linha in linhas_nf:
        linha = linha.strip()

        if re.match(r"^\d{4,5}\s", linha):
            valores = re.findall(r"\d+,\d+", linha)

            if len(valores) >= 3:
                codigo_mp = linha.split()[0]
                valor_total = float(valores[2].replace(",", "."))

                nf_mp[codigo_mp] = nf_mp.get(codigo_mp, 0) + valor_total

    # =============================
    # 2. REQUISIÇÃO (REGRA CORRETA)
    # =============================
    requisicao = []
    i = 0

    while i < len(linhas_req) - 2:
        linha_prod = linhas_req[i]
        linha_qtd = linhas_req[i + 1]
        linha_mp = linhas_req[i + 2]

        if "PRODUTO INTERMEDIÁRIO" in linha_prod and "MATÉRIA-PRIMA" in linha_mp:

            prod = re.search(r"\b\d{4,}\b", linha_prod)
            mp = re.search(r"\(M\)\s*(\d{4,})", linha_mp)
            qtd = re.search(r"\b\d+\b", linha_qtd)
            consumo = re.findall(r"\d+,\d+", linha_mp)

            if prod and mp and qtd and consumo:
                requisicao.append({
                    "produto": prod.group(0),
                    "mp": mp.group(1),
                    "qtd": int(qtd.group(0)),
                    "consumo": float(consumo[-1].replace(",", "."))
                })
                i += 3
            else:
                i += 1
        else:
            i += 1

    # =============================
    # 3. RATEIO DA MATÉRIA-PRIMA
    # =============================
    consumo_total = defaultdict(float)

    for item in requisicao:
        consumo_total[item["mp"]] += item["consumo"]

    # =============================
    # 4. CÁLCULO FINAL
    # =============================
    resultado = []

    for item in requisicao:
        mp = item["mp"]

        if mp not in nf_mp:
            preco = "Não consta na NF"
        else:
            rateio = (item["consumo"] / consumo_total[mp]) * nf_mp[mp]
            preco = round(rateio / item["qtd"], 3)

        resultado.append({
            "Código do Produto": item["produto"],
            "Preço por Peça": preco
        })

    df = pd.DataFrame(resultado)
    st.success("Processamento concluído")
    st.dataframe(df)

    st.download_button(
        label="⬇️ Baixar CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="custo_por_peca.csv",
        mime="text/csv",
        key="download_csv"
    )
