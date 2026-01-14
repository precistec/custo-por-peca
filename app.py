import streamlit as st
import pdfplumber
import pandas as pd
import re

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
    # 1. NOTA FISCAL – MP
    # =============================
    nf_mp = {}

    for linha in linhas_nf:
        linha = linha.strip()

        # linha começa com código
        if re.match(r"^\d{2,5}\s", linha):
            partes = linha.split()

            # última coluna TEM que ser valor total
            ultimo = partes[-1]

            if "," in ultimo:
                try:
                    codigo = partes[0]
                    valor_total = float(ultimo.replace(".", "").replace(",", "."))
                    nf_mp[codigo] = nf_mp.get(codigo, 0) + valor_total
                except:
                    pass

    st.subheader("DEBUG – Matérias-primas encontradas na NF")
    st.write(nf_mp)

    # =============================
    # 2. REQUISIÇÃO
    # =============================
    itens = []
    i = 0

    while i < len(linhas_req) - 2:
        p = linhas_req[i]
        q = linhas_req[i + 1]
        m = linhas_req[i + 2]

        if "PRODUTO INTERMEDIÁRIO" in p and "MATÉRIA-PRIMA" in m:
            cod_prod = re.findall(r"\b\d{4,5}\b", p)
            cod_mp = re.findall(r"\b\d{2,5}\b", m)
            qtd = re.findall(r"\b\d+\b", q)

            if cod_prod and cod_mp and qtd:
                itens.append({
                    "produto": cod_prod[0],
                    "mp": cod_mp[0],
                    "qtd": int(qtd[0]),
                    "linha_mp": m.upper()
                })
                i += 3
            else:
                i += 1
        else:
            i += 1

    # =============================
    # 3. CÁLCULO
    # =============================
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
