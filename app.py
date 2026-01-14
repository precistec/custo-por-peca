import streamlit as st
import pandas as pd
import pdfplumber
import re
from collections import defaultdict

st.set_page_config(page_title="Custo por Peça", layout="centered")
st.title("🔧 Cálculo de Custo por Peça")

# =========================
# UPLOAD
# =========================
req_file = st.file_uploader(
    "📄 Requisição (PDF ou Excel)", type=["pdf", "xlsx", "xls"]
)
nf_file = st.file_uploader(
    "🧾 Nota Fiscal (PDF ou XML)", type=["pdf", "xml"]
)

# =========================
# FUNÇÕES AUXILIARES
# =========================
def extrair_maior_numero(texto):
    """
    Extrai o MAIOR número da linha (usado para consumo em mm).
    """
    numeros = re.findall(r"\d+,\d+|\d+\.\d+|\d+", texto)
    if not numeros:
        return 0
    valores = [float(n.replace(",", ".")) for n in numeros]
    return max(valores)

def limpar_linhas(linhas):
    """
    Mantém apenas linhas que começam com código numérico
    """
    limpas = []
    for l in linhas:
        l = l.strip()
        if l and l.split()[0].isdigit():
            limpas.append(l)
    return limpas

def ler_requisicao_pdf(file):
    linhas = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            texto = page.extract_text()
            if texto:
                linhas.extend(texto.split("\n"))
    return limpar_linhas(linhas)

def ler_nf_pdf(file):
    """
    Retorna dict:
    { codigo_mp : valor_total_nf }
    """
    mp_valores = {}
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            texto = page.extract_text()
            if texto:
                for linha in texto.split("\n"):
                    # pega código MP + valor total
                    m = re.search(r"^(\d{4,}).*?(\d+,\d{2})$", linha.strip())
                    if m:
                        codigo = m.group(1)
                        valor = float(m.group(2).replace(",", "."))
                        mp_valores[codigo] = valor
    return mp_valores

# =========================
# PROCESSAMENTO
# =========================
if req_file and nf_file:
    st.success("Arquivos carregados com sucesso")

    if st.button("▶️ Calcular custo por peça"):
        produtos = []

        # ---------- REQUISIÇÃO ----------
        if req_file.name.endswith(".pdf"):
            linhas = ler_requisicao_pdf(req_file)
        else:
            df_req = pd.read_excel(req_file)
            linhas = df_req.astype(str).agg(" ".join, axis=1).tolist()
            linhas = limpar_linhas(linhas)

        for i in range(0, len(linhas) - 1, 2):
            linha_prod = linhas[i]
            linha_mp = linhas[i + 1]

            # Código do produto = PRIMEIRO elemento da linha
            codigo_produto = linha_prod.split()[0]

            # Quantidade de peças = MAIOR número da linha do produto
            qtde_pecas = int(extrair_maior_numero(linha_prod))

            # Código da MP = PRIMEIRO elemento da linha MP
            codigo_mp = linha_mp.split()[0]

            # Consumo da MP em mm
            consumo_mm = extrair_maior_numero(linha_mp)

            produtos.append({
                "produto": codigo_produto,
                "qtde": qtde_pecas,
                "mp": codigo_mp,
                "mm": consumo_mm
            })

        # ---------- NOTA FISCAL ----------
        mp_nf = ler_nf_pdf(nf_file)

        # ---------- RATEIO ----------
        consumo_total_mp = defaultdict(float)
        for p in produtos:
            consumo_total_mp[p["mp"]] += p["mm"]

        resultados = []

        for p in produtos:
            mp = p["mp"]

            # MP não existe na NF
            if mp not in mp_nf:
                resultados.append({
                    "Código do Produto": p["produto"],
                    "Preço por Peça": "Não consta na NF"
                })
                continue

            valor_total_mp = mp_nf[mp]

            # MP exclusiva
            if consumo_total_mp[mp] == p["mm"]:
                preco = valor_total_mp / p["qtde"]
            else:
                # MP compartilhada
                custo_por_mm = valor_total_mp / consumo_total_mp[mp]
                preco = (custo_por_mm * p["mm"]) / p["qtde"]

            resultados.append({
                "Código do Produto": p["produto"],
                "Preço por Peça": round(preco, 2)
            })

        # ---------- RESULTADO ----------
        df_result = pd.DataFrame(resultados)

        st.subheader("📊 Resultado Final")
        st.dataframe(df_result, use_container_width=True)

        # ---------- EXPORTAÇÃO ----------
        csv = df_result.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Baixar CSV",
            csv,
            "custo_por_peca.csv",
            "text/csv"
        )
