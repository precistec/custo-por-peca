import streamlit as st
import pandas as pd
import pdfplumber
import re
from collections import defaultdict

st.set_page_config(page_title="Custo por Peça", layout="centered")
st.title("🔧 Cálculo de Custo por Peça")

req_file = st.file_uploader("📄 Requisição (PDF ou Excel)", type=["xlsx", "xls", "pdf"])
nf_file = st.file_uploader("🧾 Nota Fiscal (PDF ou XML)", type=["xlsx", "xls", "pdf", "xml"])

# ---------- FUNÇÕES ----------
def extrair_numero(texto):
    nums = re.findall(r"\d+,\d+|\d+\.\d+|\d+", texto)
    if not nums:
        return 0
    valores = [float(n.replace(",", ".")) for n in nums]
    return max(valores)

def limpar_linhas(linhas):
    return [l for l in linhas if re.search(r"\d{4,}", l)]

def ler_requisicao_pdf(file):
    linhas = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            texto = page.extract_text()
            if texto:
                linhas.extend(texto.split("\n"))
    return limpar_linhas(linhas)

def ler_nf_pdf(file):
    mp_valores = {}
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            texto = page.extract_text()
            if texto:
                for linha in texto.split("\n"):
                    m = re.search(r"(\d{4,}).*(\d+,\d{2})$", linha)
                    if m:
                        codigo = m.group(1)
                        valor = float(m.group(2).replace(",", "."))
                        mp_valores[codigo] = valor
    return mp_valores

# ---------- PROCESSAMENTO ----------
if req_file and nf_file:
    st.success("Arquivos carregados!")

    if st.button("▶️ Calcular custo por peça"):
        produtos = []

        # ===== REQUISIÇÃO =====
        linhas = ler_requisicao_pdf(req_file)

        for i in range(0, len(linhas) - 1, 2):
            prod_linha = linhas[i]
            mp_linha = linhas[i + 1]

            prod_codigo = re.search(r"\d{4,}", prod_linha).group()
            qtde_pecas = int(extrair_numero(prod_linha))

            mp_codigo = re.search(r"\d{4,}", mp_linha).group()
            consumo_mm = extrair_numero(mp_linha)

            produtos.append({
                "produto": prod_codigo,
                "qtde": qtde_pecas,
                "mp": mp_codigo,
                "mm": consumo_mm
            })

        # ===== NOTA FISCAL =====
        mp_nf = ler_nf_pdf(nf_file)

        # ===== RATEIO =====
        consumo_total_mp = defaultdict(float)
        for p in produtos:
            consumo_total_mp[p["mp"]] += p["mm"]

        resultados = []

        for p in produtos:
            mp = p["mp"]

            if mp not in mp_nf:
                resultados.append({
                    "Código do Produto": p["produto"],
                    "Preço por Peça": "Não consta na NF"
                })
                continue

            valor_total_mp = mp_nf[mp]

            if consumo_total_mp[mp] == p["mm"]:
                preco = valor_total_mp / p["qtde"]
            else:
                custo_mm = valor_total_mp / consumo_total_mp[mp]
                preco = (custo_mm * p["mm"]) / p["qtde"]

            resultados.append({
                "Código do Produto": p["produto"],
                "Preço por Peça": round(preco, 2)
            })

        df_result = pd.DataFrame(resultados)

        st.subheader("📊 Resultado Final")
        st.dataframe(df_result, use_container_width=True)
