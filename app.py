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

    # ======================================================
    # 1. LER NOTA FISCAL → SOMAR VALOR TOTAL POR MP
    # ======================================================
    nf_mp = {}

    for linha in linhas_nf:
        linha = linha.strip()

        # começa com código numérico
        if re.match(r"^\d{4,5}\s", linha):
            valores = re.findall(r"\d+,\d+", linha)

            # precisa ter quantidade, unitário e total
            if len(valores) >= 3:
                codigo_mp = linha.split()[0]
                valor_total = float(valores[2].replace(",", "."))

                if codigo_mp in nf_mp:
                    nf_mp[codigo_mp] += valor_total
                else:
                    nf_mp[codigo_mp] = valor_total

    # ======================================================
    # 2. LER REQUISIÇÃO (PRODUTO / QTD / MP / CONSUMO)
    # ======================================================
    requisicao = []
    i = 0

    while i < len(linhas_req) - 2:
        linha_prod = linhas_req[i].strip()
        linha_qtd = linhas_req[i + 1].strip()
        linha_mp = linhas_req[i + 2].strip()

        if "PRODUTO INTERMEDIÁRIO" in linha_prod and "MATÉRIA-PRIMA" in linha_mp:

            prod_match = re.search(r"\b\d{4,}\b", linha_prod)
            mp_match = re.search(r"\(M\)\s*(\d{4,})", linha_mp)

            try:
                qtd_pecas = int(linha_qtd)
            except:
                qtd_pecas = 0

            consumos = re.findall(r"\d+,\d+", linha_mp)

            if prod_match and mp_match and qtd_pecas > 0 and consumos:
                requisicao.append({
                    "produto": prod_match.group(0),
                    "mp": mp_match.group(1),
                    "qtd": qtd_pecas,
                    "consumo": float(consumos[-1].replace(",", "."))
                })
                i += 3
            else:
                i += 1
        else:
            i += 1

    # ======================================================
    # 3. SOMAR CONSUMO TOTAL POR MATÉRIA-PRIMA
    # ======================================================
    consumo_total = defaultdict(float)

    for item in requisicao:
        consumo_total[item["mp"]] += item["consumo"]

    # ======================================================
    # 4. CALCULAR PREÇO POR PEÇA
    # ======================================================
    resultado = []

    for item in requisicao:
        produto = item["produto"]
        mp = item["mp"]
        qtd = item["qtd"]
        consumo = item["consumo"]

        if mp not in nf_mp:
            preco = "Não consta na NF"
        else:
            valor_total_mp = nf_mp[mp]

            # MP usada em apenas um produto
            if consumo_total[mp] == consumo:
                preco = round(valor_total_mp / qtd, 3)
            else:
                rateio = (consumo / consumo_total[mp]) * valor_total_mp
                preco = round(rateio / qtd, 3)

        resultado.append({
            "Código do Produto": produto,
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
        key="download_csv_final"
    )
