import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Precistec • NF x Requisição", layout="wide")

st.title("Precistec – Leitura de Nota Fiscal e Requisição")
st.caption("Separação correta dos dados (sem cálculo)")

# =========================
# INPUTS
# =========================
col1, col2 = st.columns(2)

with col1:
    nf_texto = st.text_area(
        "Cole aqui a NOTA FISCAL (texto bruto)",
        height=350
    )

with col2:
    req_texto = st.text_area(
        "Cole aqui a REQUISIÇÃO (texto bruto)",
        height=350
    )

# =========================
# FUNÇÃO: LER NOTA FISCAL
# =========================
def ler_nf(texto):
    linhas = texto.splitlines()
    dados = []

    for linha in linhas:
        linha = linha.strip()

        # começa com código numérico
        if not re.match(r"^\d{4,}", linha):
            continue

        partes = re.split(r"\s{2,}", linha)

        if len(partes) < 8:
            continue

        try:
            codigo = partes[0]
            descricao = partes[1]
            unidade = partes[5]
            quantidade = partes[6].replace(",", ".")
            valor_total = partes[8].replace(".", "").replace(",", ".")

            if unidade not in ["M", "UNI", "UN"]:
                continue

            dados.append({
                "CÓDIGO": codigo,
                "DESCRIÇÃO": descricao,
                "UNIDADE": unidade,
                "QUANTIDADE": float(quantidade),
                "VALOR TOTAL (NF)": float(valor_total)
            })

        except:
            continue

    return pd.DataFrame(dados)


# =========================
# FUNÇÃO: LER REQUISIÇÃO
# =========================
def ler_requisicao(texto):
    linhas = [l.strip() for l in texto.splitlines() if l.strip()]
    dados = []

    i = 0
    while i < len(linhas) - 1:
        if linhas[i].startswith("PRODUTO INTERMEDIÁRIO"):
            prod_linha = linhas[i]
            mp_linha = linhas[i + 1]

            prod_partes = prod_linha.split()
            mp_partes = mp_linha.split()

            try:
                produto_codigo = prod_partes[3]
                produto_desc = " ".join(prod_partes[4:-1])
                produto_qtde = prod_partes[-1]

                mp_codigo = mp_partes[2]
                mp_desc = " ".join(mp_partes[3:-1])
                mp_qtde = mp_partes[-1]

                dados.append({
                    "PRODUTO CÓDIGO": produto_codigo,
                    "PRODUTO DESCRIÇÃO": produto_desc,
                    "QTDE PRODUTO": produto_qtde,
                    "MP CÓDIGO": mp_codigo,
                    "MP DESCRIÇÃO": mp_desc,
                    "QTDE MP (REQ)": mp_qtde
                })

                i += 2
            except:
                i += 1
        else:
            i += 1

    return pd.DataFrame(dados)


# =========================
# PROCESSAMENTO
# =========================
if st.button("Processar dados"):
    st.divider()

    st.subheader("📄 Nota Fiscal – Linhas válidas")
    df_nf = ler_nf(nf_texto)
    st.dataframe(df_nf, use_container_width=True)

    st.subheader("🧾 Requisição – Produto x Matéria-prima")
    df_req = ler_requisicao(req_texto)
    st.dataframe(df_req, use_container_width=True)

    st.success("Leitura concluída sem misturar dados.")
