import streamlit as st
import pdfplumber
import pandas as pd
import re
from collections import defaultdict

st.set_page_config(page_title="Custo por Peça (PDF/CSV/XLS)", layout="centered")
st.title("Cálculo de Custo por Peça")

# Aceita PDF, XLS, XLSX, CSV
nf_file = st.file_uploader("📄 Nota Fiscal (PDF, CSV ou Excel)", type=["pdf", "csv", "xlsx", "xls"])
req_file = st.file_uploader("📄 Requisição (PDF, CSV ou Excel)", type=["pdf", "csv", "xlsx", "xls"])

# =========================
# Funções auxiliares
# =========================
def extrair_linhas_pdf(pdf):
    linhas = []
    with pdfplumber.open(pdf) as p:
        for page in p.pages:
            texto = page.extract_text()
            if texto:
                linhas.extend(texto.split("\n"))
    return linhas

def ler_nota_fiscal(file):
    nf_mp = defaultdict(float)

    if file.name.endswith(".pdf"):
        linhas = extrair_linhas_pdf(file)
        codigo_atual = None
        for linha in linhas:
            linha = linha.strip()
            match_codigo = re.match(r"^(\d{2,5})\b", linha)
            if match_codigo:
                codigo_atual = match_codigo.group(1)
            valores = re.findall(r"\d+,\d{2}", linha)
            if codigo_atual and valores:
                try:
                    valor = float(valores[-1].replace(",", "."))
                    nf_mp[codigo_atual] += valor
                    codigo_atual = None
                except:
                    continue
    else:  # CSV ou Excel
        try:
            if file.name.endswith((".xlsx", ".xls")):
                df = pd.read_excel(file)
            else:
                df = pd.read_csv(file, sep=None, engine='python', encoding='utf-8')
        except Exception:
            df = pd.read_csv(file, sep=None, engine='python', encoding='ISO-8859-1')

        df = df.rename(columns=lambda x: x.strip())
        if 'Código' not in df.columns or 'Valor Total' not in df.columns:
            st.error("A Nota Fiscal precisa ter colunas: Código e Valor Total")
            st.stop()

        for idx, row in df.iterrows():
            codigo = str(row['Código']).strip()
            valor_total = float(row['Valor Total'])
            nf_mp[codigo] += valor_total

    return nf_mp

def ler_requisicao(file):
    itens = []

    if file.name.endswith(".pdf"):
        linhas = extrair_linhas_pdf(file)
        i = 0
        while i < len(linhas) - 2:
            prod = linhas[i]
            qtd = linhas[i + 1]
            mp = linhas[i + 2]
            if "PRODUTO INTERMEDIÁRIO" in prod and "MATÉRIA-PRIMA" in mp:
                cod_prod = re.findall(r"\b\d{4,5}\b", prod)
                cod_mp = re.findall(r"\b\d{2,5}\b", mp)
                qtd_prod = re.findall(r"\b\d+\b", qtd)
                if cod_prod and cod_mp and qtd_prod:
                    itens.append({
                        "produto": cod_prod[0],
                        "mp": cod_mp[0],
                        "qtd": int(qtd_prod[0]),
                        "linha_mp": mp.upper()
                    })
                    i += 3
                else:
                    i += 1
            else:
                i += 1
    else:  # CSV ou Excel
        try:
            if file.name.endswith((".xlsx", ".xls")):
                df = pd.read_excel(file)
            else:
                df = pd.read_csv(file, sep=None, engine='python', encoding='utf-8')
        except Exception:
            df = pd.read_csv(file, sep=None, engine='python', encoding='ISO-8859-1')

        df = df.rename(columns=lambda x: x.strip())
        for col in ['Produto', 'Qtd', 'MP']:
            if col not in df.columns:
                st.error(f"A Requisição precisa ter a coluna: {col}")
                st.stop()
        for idx, row in df.iterrows():
            itens.append({
                "produto": str(row['Produto']),
                "mp": str(row['MP']),
                "qtd": int(row['Qtd']),
                "linha_mp": str(row['MP']).upper()
            })
    return itens

# =========================
# Processamento
# =========================
if st.button("🔧 Processar"):

    if not nf_file or not req_file:
        st.error("Envie ambos os arquivos.")
        st.stop()

    # Ler Nota Fiscal
    nf_mp = ler_nota_fiscal(nf_file)
    st.subheader("DEBUG – Matérias-primas da NF")
    st.write(dict(nf_mp))

    # Ler Requisição
    itens = ler_requisicao(req_file)

    # Calcular preço por peça
    resultado = []
    for item in itens:
        produto = item["produto"]
        mp = item["mp"]
        qtd = item["qtd"]
        linha_mp = item["linha_mp"]

        if "ALMOXARIFADO" in linha_mp:
            preco = "ALMOXARIFADO"
        elif mp not in nf_mp or nf_mp[mp] == 0:
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
