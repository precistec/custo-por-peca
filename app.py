import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Precistec | Custo por Peça", layout="wide")

st.title("Precistec – Cálculo de Custo por Peça")
st.caption("Cole a REQUISIÇÃO e a NOTA FISCAL exatamente como recebidas")

# =========================
# ENTRADAS
# =========================
req_text = st.text_area(
    "REQUISIÇÃO (cole aqui)",
    height=300,
    placeholder="Cole a requisição exatamente como ela é..."
)

nf_text = st.text_area(
    "NOTA FISCAL (cole aqui)",
    height=300,
    placeholder="Cole a nota fiscal exatamente como ela é..."
)

processar = st.button("PROCESSAR")

# =========================
# FUNÇÕES
# =========================
def parse_requisicao(texto):
    linhas = texto.splitlines()
    dados = []

    produto_atual = None
    qtde_produto = None

    for l in linhas:
        l = l.strip()
        if not l:
            continue

        # Produto intermediário
        if "PRODUTO INTERMEDIÁRIO" in l:
            partes = l.split()
            try:
                produto_atual = partes[3]
                qtde_produto = float(partes[-1].replace(",", "."))
            except:
                produto_atual = None
                qtde_produto = None

        # Matéria-prima
        if "MATÉRIA-PRIMA" in l and produto_atual:
            partes = l.split()
            try:
                cod_mp = partes[3]
                qtde_mp = float(partes[-1].replace(",", "."))

                dados.append({
                    "cod_produto": produto_atual,
                    "qtde_produto": qtde_produto,
                    "cod_mp": cod_mp,
                    "qtde_mp_req": qtde_mp
                })
            except:
                pass

    return pd.DataFrame(dados)


def parse_nf(texto):
    linhas = texto.splitlines()
    dados = []

    for l in linhas:
        l = l.replace("\t", " ").strip()
        if not l:
            continue

        # ignora linhas sem números
        if not re.search(r"\d", l):
            continue

        partes = re.split(r"\s{2,}", l)
        partes = [p.strip() for p in partes if p.strip()]

        if len(partes) < 7:
            continue

        try:
            codigo = partes[0].split()[0]
            descricao = partes[1]
            unidade = partes[5]
            qtde_nf = float(partes[6].replace(".", "").replace(",", "."))
            valor_total = float(partes[8].replace(".", "").replace(",", "."))

            dados.append({
                "cod_mp": codigo,
                "desc_mp_nf": descricao,
                "unidade": unidade,
                "qtde_nf": qtde_nf,
                "valor_total_nf": valor_total
            })
        except:
            continue

    return pd.DataFrame(dados)


# =========================
# PROCESSAMENTO
# =========================
if processar:

    st.subheader("DEBUG — Texto da Requisição")
    st.text(req_text)

    st.subheader("DEBUG — Texto da Nota Fiscal")
    st.text(nf_text)

    req_df = parse_requisicao(req_text)
    nf_df = parse_nf(nf_text)

    st.subheader("DEBUG — Requisição Estruturada")
    st.dataframe(req_df)

    st.subheader("DEBUG — Nota Fiscal Estruturada")
    st.dataframe(nf_df)

    if req_df.empty or nf_df.empty:
        st.error("❌ Não foi possível interpretar a requisição ou a NF. Verifique o texto colado.")
        st.stop()

    resultado = []

    for _, r in req_df.iterrows():
        mp_nf = nf_df[nf_df["cod_mp"] == r["cod_mp"]]

        if mp_nf.empty:
            resultado.append({
                "CÓDIGO": r["cod_produto"],
                "QTDE": r["qtde_produto"],
                "R$/PEÇA": 0,
                "TOTAL (R$)": 0,
                "DIVERGÊNCIA": "Matéria-prima não consta na Nota Fiscal"
            })
            continue

        mp_nf = mp_nf.iloc[0]

        # Regra de unidade
        if mp_nf["unidade"].upper() not in ["M", "METRO", "METROS"]:
            resultado.append({
                "CÓDIGO": r["cod_produto"],
                "QTDE": r["qtde_produto"],
                "R$/PEÇA": "—",
                "TOTAL (R$)": "—",
                "DIVERGÊNCIA": "Item com valor unitário (UNI/UN)"
            })
            continue

        # Regra de rateio
        valor_total_mp = mp_nf["valor_total_nf"]

        preco_peca = valor_total_mp / r["qtde_produto"]
        total = preco_peca * r["qtde_produto"]

        divergencia = "—"
        if abs(mp_nf["qtde_nf"] - r["qtde_mp_req"]) > 0.0001:
            divergencia = "Quantidade de matéria-prima da requisição diferente da Nota Fiscal"

        resultado.append({
            "CÓDIGO": r["cod_produto"],
            "QTDE": r["qtde_produto"],
            "R$/PEÇA": round(preco_peca, 4),
            "TOTAL (R$)": round(total, 2),
            "DIVERGÊNCIA": divergencia
        })

    final_df = pd.DataFrame(resultado)

    st.subheader("TABELA FINAL — Pronta para Word / Impressão")
    st.dataframe(final_df)

    # Conferência
    soma_total = final_df[final_df["TOTAL (R$)"].apply(lambda x: isinstance(x, (int, float)))]["TOTAL (R$)"].sum()

    st.subheader("CONFERÊNCIA")
    st.write(f"**Soma da tabela (itens monetários): R$ {soma_total:,.2f}**")
