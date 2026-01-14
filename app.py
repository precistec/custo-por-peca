import streamlit as st
import pandas as pd
import pdfplumber
from collections import defaultdict
import re

st.set_page_config(page_title="Cálculo de Custo por Peça", layout="centered")

st.title("Cálculo de Preço por Peça")
st.write("Faça o upload da Nota Fiscal e da Requisição")

# =========================
# UPLOAD DOS ARQUIVOS
# =========================

nf_file = st.file_uploader("📄 Nota Fiscal (PDF)", type="pdf")
req_file = st.file_uploader("📄 Requisição (PDF)", type="pdf")

# =========================
# FUNÇÃO PARA LER PDF
# =========================

def extrair_linhas_pdf(pdf_file):
    linhas = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            texto = page.extract_text()
            if texto:
                linhas.extend(texto.split("\n"))
    return linhas

# =========================
# BOTÃO DE PROCESSAMENTO
# =========================

if st.button("🔧 Processar arquivos"):

    if not nf_file or not req_file:
        st.error("Envie os dois arquivos primeiro.")
        st.stop()

    # =========================
    # LER PDFs
    # =========================

    linhas_nf = extrair_linhas_pdf(nf_file)
    linhas_req = extrair_linhas_pdf(req_file)
    st.subheader("DEBUG – Primeiras linhas da Nota Fiscal")
    st.write(linhas_nf[:20])

    st.subheader("DEBUG – Primeiras linhas da Requisição")
    st.write(linhas_req[:20])


    st.write("📌 PDFs carregados com sucesso")

    # =========================
    # EXTRAIR NOTA FISCAL (MP)
    # =========================

    nota_fiscal = {}

    for linha in linhas_nf:
        # Exemplo esperado: CODIGO | QUANTIDADE | VALOR TOTAL
        numeros = re.findall(r"\d+[,\.]?\d*", linha)

        if len(numeros) >= 2:
            codigo = numeros[0]
            valor_total = float(numeros[-1].replace(",", "."))

            # NF só tem MP
            nota_fiscal[codigo] = valor_total

    # =========================
    # EXTRAIR REQUISIÇÃO
    # =========================

    requisicao = []

    i = 0
    while i < len(linhas_req) - 1:
        linha_produto = linhas_req[i].strip()
        linha_mp = linhas_req[i + 1].strip()

        # Produto = primeira linha
        prod_match = re.match(r"^(\d+)", linha_produto)
        mp_match = re.match(r"^(\d+)", linha_mp)

        if prod_match and mp_match:
            produto_codigo = prod_match.group(1)
            mp_codigo = mp_match.group(1)

            # Quantidade de peças
            qtd_match = re.search(r"(\d+)\s*(pcs|peças|un)", linha_produto, re.IGNORECASE)
            quantidade_pecas = int(qtd_match.group(1)) if qtd_match else 1

            # Consumo MP em mm
            consumo_match = re.search(r"(\d+)\s*mm", linha_mp, re.IGNORECASE)
            consumo_mm = int(consumo_match.group(1)) if consumo_match else 0

            requisicao.append({
                "produto": produto_codigo,
                "mp": mp_codigo,
                "qtd_pecas": quantidade_pecas,
                "consumo_mm": consumo_mm
            })

            i += 2
        else:
            i += 1

    # =========================
    # RATEIO DE MP
    # =========================

    consumo_total_mp = defaultdict(int)

    for item in requisicao:
        consumo_total_mp[item["mp"]] += item["consumo_mm"]

    # =========================
    # CALCULAR PREÇO POR PEÇA
    # =========================

    resultado = []

    for item in requisicao:
        produto = item["produto"]
        mp = item["mp"]
        qtd = item["qtd_pecas"]
        consumo = item["consumo_mm"]

        if mp not in nota_fiscal or consumo_total_mp[mp] == 0:
            preco_peca = "Não consta na NF"
        else:
            valor_total_mp = nota_fiscal[mp]
            valor_rateado = (consumo / consumo_total_mp[mp]) * valor_total_mp
            preco_peca = round(valor_rateado / qtd, 3)

        resultado.append({
            "Código do Produto": produto,
            "Preço por Peça": preco_peca
        })

    # =========================
    # GERAR RESULTADO
    # =========================

    df = pd.DataFrame(resultado)

    st.success("Cálculo finalizado")
    st.dataframe(df)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Baixar CSV",
        csv,
        "custo_por_peca.csv",
        "text/csv"
    )
