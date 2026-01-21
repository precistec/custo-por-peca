import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Precistec – Custo por Peça", layout="wide")

st.title("Precistec – Apuração de Custo por Peça")
st.caption("Cruzamento Requisição x Nota Fiscal • Regra definitiva")

# =========================
# INPUTS
# =========================
req_text = st.text_area("📋 Cole aqui a REQUISIÇÃO", height=300)
nf_text = st.text_area("🧾 Cole aqui a NOTA FISCAL", height=300)

def parse_requisicao(texto):
    linhas = texto.splitlines()
    dados = []
    produto_atual = None

    for l in linhas:
        if "PRODUTO INTERMEDIÁRIO" in l:
            partes = l.split()
            codigo = partes[3]
            qtde = float(partes[-1].replace(",", "."))
            descricao = " ".join(partes[4:-1])
            produto_atual = {
                "cod_prod": codigo,
                "desc_prod": descricao,
                "qtde_prod": qtde
            }

        if "MATÉRIA-PRIMA" in l and produto_atual:
            partes = l.split()
            cod_mp = partes[3]
            qtde_mp = float(partes[-1].replace(",", "."))
            desc_mp = " ".join(partes[4:-1])

            dados.append({
                **produto_atual,
                "cod_mp": cod_mp,
                "desc_mp": desc_mp,
                "qtde_mp_req": qtde_mp
            })

    return pd.DataFrame(dados)

def parse_nf(texto):
    linhas = texto.splitlines()
    dados = []

    for l in linhas:
        if re.match(r"^\d{5}", l.strip()):
            partes = l.split()
            dados.append({
                "cod_mp": partes[0],
                "desc_mp_nf": partes[1],
                "unidade": partes[5],
                "qtde_nf": float(partes[6].replace(",", ".")),
                "valor_total": float(partes[8].replace(",", "."))
            })

    return pd.DataFrame(dados)

# =========================
# PROCESSAMENTO
# =========================
if st.button("🚀 Gerar tabela final"):
    if not req_text or not nf_text:
        st.warning("Cole a requisição e a nota fiscal.")
    else:
        req_df = parse_requisicao(req_text)
        nf_df = parse_nf(nf_text)

        tabela = []
        total_nf = nf_df["valor_total"].sum()
        total_apurado = 0

        for _, r in req_df.iterrows():
            mp_nf = nf_df[nf_df["cod_mp"] == r["cod_mp"]]

            if mp_nf.empty:
                tabela.append({
                    "CÓDIGO PRODUTO": r["cod_prod"],
                    "DESCRIÇÃO PRODUTO": r["desc_prod"],
                    "QTDE PEÇAS": r["qtde_prod"],
                    "MP CÓDIGO": r["cod_mp"],
                    "MP DESCRIÇÃO": r["desc_mp"],
                    "UNIDADE NF": "-",
                    "R$/PEÇA": "—",
                    "TOTAL (R$)": 0.00,
                    "DIVERGÊNCIA": "Matéria-prima não consta na Nota Fiscal"
                })
                continue

            mp_nf = mp_nf.iloc[0]

            # REGRA DE UNIDADE
            if mp_nf["unidade"] != "M":
                tabela.append({
                    "CÓDIGO PRODUTO": r["cod_prod"],
                    "DESCRIÇÃO PRODUTO": r["desc_prod"],
                    "QTDE PEÇAS": r["qtde_prod"],
                    "MP CÓDIGO": r["cod_mp"],
                    "MP DESCRIÇÃO": r["desc_mp"],
                    "UNIDADE NF": mp_nf["unidade"],
                    "R$/PEÇA": "—",
                    "TOTAL (R$)": "—",
                    "DIVERGÊNCIA": "Item com valor unitário (não rateável)"
                })
                total_apurado += mp_nf["valor_total"]
                continue

            # REGRA METRO
            valor_total = mp_nf["valor_total"]
            preco_peca = valor_total / r["qtde_prod"]

            tabela.append({
                "CÓDIGO PRODUTO": r["cod_prod"],
                "DESCRIÇÃO PRODUTO": r["desc_prod"],
                "QTDE PEÇAS": r["qtde_prod"],
                "MP CÓDIGO": r["cod_mp"],
                "MP DESCRIÇÃO": r["desc_mp"],
                "UNIDADE NF": "M",
                "R$/PEÇA": round(preco_peca, 4),
                "TOTAL (R$)": round(valor_total, 2),
                "DIVERGÊNCIA": (
                    "Quantidade MP NF ≠ requisição"
                    if abs(mp_nf["qtde_nf"] - r["qtde_mp_req"]) > 0.0001
                    else "—"
                )
            })

            total_apurado += valor_total

        df_final = pd.DataFrame(tabela)

        st.subheader("📊 Tabela Final")
        st.dataframe(df_final, use_container_width=True)

        st.subheader("🔎 Conferência")
        st.write(f"**Total NF:** R$ {total_nf:,.2f}")
        st.write(f"**Total Apurado:** R$ {total_apurado:,.2f}")

        if round(total_nf, 2) == round(total_apurado, 2):
            st.success("✔ Total conferido com a Nota Fiscal")
        else:
            st.error("❌ Divergência entre NF e tabela – ver coluna DIVERGÊNCIA")
