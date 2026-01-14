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

    # =============================
    # 1. EXTRAIR LINHAS
    # =============================
    linhas_nf = extrair_linhas(nf_file)
    linhas_req = extrair_linhas(req_file)

# =============================
# 2. EXTRAIR MATÉRIA-PRIMA DA NF
# =============================
nf_mp = {}

for linha in linhas_nf:
    linha = linha.strip()

    # só aceita linhas de MATÉRIA-PRIMA (unidade M)
    if re.match(r"^\d{4,5}\s", linha) and " M " in linha:

        valores = re.findall(r"\d+,\d+", linha)

        # precisa ter quantidade, unitário e total
        if len(valores) >= 3:
            codigo_mp = linha.split()[0]

            # VALOR TOTAL é o terceiro número
            valor_total = float(valores[2].replace(",", "."))

            # soma se aparecer mais de uma vez
            if codigo_mp in nf_mp:
                nf_mp[codigo_mp] += valor_total
            else:
                nf_mp[codigo_mp] = valor_total

             

    # =============================
    # 3. EXTRAIR REQUISIÇÃO
    # =============================
    requisicao = []
    i = 0

    while i < len(linhas_req) - 2:
        linha_prod = linhas_req[i]
        linha_qtd = linhas_req[i + 1]
        linha_mp = linhas_req[i + 2]

        if "PRODUTO INTERMEDIÁRIO" in linha_prod and "MATÉRIA-PRIMA" in linha_mp:

            prod_codigo = re.findall(r"\b\d{4,}\b", linha_prod)
            mp_codigo = re.findall(r"\b\d{4,}\b", linha_mp)
            qtd_pecas = re.findall(r"\d+", linha_qtd)
            consumos = re.findall(r"\d+,\d+", linha_mp)

            if prod_codigo and mp_codigo and qtd_pecas and consumos:
                consumo_real = float(consumos[-1].replace(",", "."))

                requisicao.append({
                    "produto": prod_codigo[0],
                    "mp": mp_codigo[0],
                    "qtd": int(qtd_pecas[0]),
                    "consumo": consumo_real
                })
                i += 3
            else:
                i += 1
        else:
            i += 1

    # =============================
    # 4. SOMAR CONSUMO TOTAL POR MP
    # =============================
    consumo_total = defaultdict(float)

    for item in requisicao:
        consumo_total[item["mp"]] += item["consumo"]

    # =============================
    # 5. CALCULAR PREÇO POR PEÇA
    # =============================
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
            rateio = (consumo / consumo_total[mp]) * valor_total_mp
            preco = round(rateio / qtd, 3)

        resultado.append({
            "Código do Produto": produto,
            "Preço por Peça": preco
        })

    # =============================
    # 6. EXIBIR RESULTADO
    # =============================
    df = pd.DataFrame(resultado)

    st.success("Processamento concluído com sucesso")
    st.dataframe(df)

st.download_button(
    label="⬇️ Baixar CSV",
    data=df.to_csv(index=False).encode("utf-8"),
    file_name="custo_por_peca.csv",
    mime="text/csv",
    key="download_csv_unico"
)

