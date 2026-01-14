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

    st.subheader("DEBUG – NF COMPLETA (linhas 40 a 120)")
    st.write(linhas_nf[40:120])


    # =============================
    # 1. EXTRAIR ITENS DA NF (MP)
    # =============================
    nf_mp = {}

    for linha in linhas_nf:
        # Exemplo esperado: 14592 ... 0,130 ... 5,34
# =============================
# EXTRAIR ITENS DA NOTA FISCAL
# =============================
    nf_mp = {}

    for linha in linhas_nf:
        linha = linha.strip()

    # linha precisa começar com código da MP
    if re.match(r"^\d{4,5}\s", linha):
        partes = linha.split()
        codigo_mp = partes[0]

        # pegar todos os valores decimais da linha
        valores = re.findall(r"\d+,\d+", linha)

        # precisa ter pelo menos quantidade, unitário e total
        if len(valores) >= 3:
            valor_total = float(valores[-1].replace(",", "."))
            nf_mp[codigo_mp] = valor_total


        if cod and len(valores) >= 2:
            codigo_mp = cod[0]
            valor_total = float(valores[-1].replace(",", "."))
            nf_mp[codigo_mp] = valor_total

    # =============================
    # 2. EXTRAIR REQUISIÇÃO
    # =============================
    requisicao = []
    i = 0

    while i < len(linhas_req) - 3:
        linha_prod = linhas_req[i]
        linha_qtd = linhas_req[i + 1]
        linha_mp = linhas_req[i + 2]

        if "PRODUTO INTERMEDIÁRIO" in linha_prod and "MATÉRIA-PRIMA" in linha_mp:
            prod_codigo = re.findall(r"\b\d{4,}\b", linha_prod)
            mp_codigo = re.findall(r"\b\d{4,}\b", linha_mp)

            qtd_pecas = re.findall(r"\d+", linha_qtd)
            consumo = re.findall(r"\d+,\d+", linha_mp)

            if prod_codigo and mp_codigo and qtd_pecas and consumo:
                requisicao.append({
                    "produto": prod_codigo[0],
                    "mp": mp_codigo[0],
                    "qtd": int(qtd_pecas[0]),
                    "consumo": float(consumo[-1].replace(",", "."))
                })
                i += 3
            else:
                i += 1
        else:
            i += 1

    # =============================
    # 3. RATEIO DA MP
    # =============================
    consumo_total = defaultdict(float)
    for item in requisicao:
        consumo_total[item["mp"]] += item["consumo"]

    # =============================
    # 4. CÁLCULO FINAL
    # =============================
    resultado = []

    for item in requisicao:
        prod = item["produto"]
        mp = item["mp"]
        qtd = item["qtd"]
        cons = item["consumo"]

        if mp not in nf_mp:
            preco = "Não consta na NF"
        else:
            valor_total_mp = nf_mp[mp]
            rateio = (cons / consumo_total[mp]) * valor_total_mp
            preco = round(rateio / qtd, 3)

        resultado.append({
            "Código do Produto": prod,
            "Preço por Peça": preco
        })

    df = pd.DataFrame(resultado)
    st.success("Processamento concluído")
    st.dataframe(df)

    st.download_button(
        "⬇️ Baixar CSV",
        df.to_csv(index=False).encode("utf-8"),
        "custo_por_peca.csv",
        "text/csv"
    )
