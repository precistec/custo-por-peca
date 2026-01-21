import streamlit as st
import pandas as pd

st.set_page_config(page_title="Cálculo de Custo por Peça - Precistec", layout="wide")
st.title("Cálculo de Custo por Peça - Precistec")

# --- Entrada de texto ---
st.subheader("Cole a Requisição")
req_text = st.text_area("Requisição", height=300)

st.subheader("Cole a Nota Fiscal")
nf_text = st.text_area("Nota Fiscal", height=300)

# --- Parsing da Requisição ---
def parse_requisicao(text):
    linhas = text.split("\n")
    produtos = []
    i = 0
    while i < len(linhas):
        if linhas[i].startswith("PRODUTO INTERMEDIÁRIO"):
            partes = linhas[i].split()
            produto_codigo = partes[1]
            produto_descricao = " ".join(partes[2:-1])
            produto_qtde = float(partes[-1].replace(",", "."))
            i += 1
            if i < len(linhas) and linhas[i].startswith("MATÉRIA-PRIMA"):
                mp_partes = linhas[i].split()
                mp_codigo = mp_partes[1]
                mp_descricao = " ".join(mp_partes[2:-1])
                mp_qtde = float(mp_partes[-1].replace(",", "."))
            else:
                mp_codigo = None
                mp_descricao = None
                mp_qtde = 0
            produtos.append({
                "produto_codigo": produto_codigo,
                "produto_descricao": produto_descricao,
                "produto_qtde": produto_qtde,
                "mp_codigo": mp_codigo,
                "mp_descricao": mp_descricao,
                "mp_qtde": mp_qtde
            })
        i += 1
    return pd.DataFrame(produtos)

# --- Parsing da Nota Fiscal ---
def parse_nf(text):
    linhas = text.split("\n")
    nf_items = []
    for linha in linhas:
        if not linha.strip() or linha.startswith("CÓDIGO") or linha.startswith("AMAM"):
            continue
        partes = linha.split()
        try:
            codigo = partes[0]
            # NCM, CST, CFOP, UNI
            ncm = partes[2]
            uni = partes[5]
            qtde = float(partes[6].replace(",", "."))
            vunit = float(partes[7].replace(",", "."))
            valor_total = float(partes[8].replace(",", "."))
            nf_items.append({
                "codigo": codigo,
                "qtde_nf": qtde,
                "valor_unit_nf": vunit,
                "valor_total_nf": valor_total,
                "unidade": uni
            })
        except:
            continue
    return pd.DataFrame(nf_items)

# --- Calcular preço por peça ---
def calcular_custo(req_df, nf_df):
    resultados = []

    nf_agrupada = nf_df.groupby("codigo").agg({
        "valor_total_nf": "sum",
        "qtde_nf": "sum",
        "unidade": "first"
    }).reset_index()

    for idx, row in req_df.iterrows():
        mp_info = nf_agrupada[nf_agrupada["codigo"] == row["mp_codigo"]]
        if mp_info.empty:
            preco_peca = "Não consta na NF"
            total = "Não consta na NF"
            divergencia = "MP não consta na NF"
        else:
            qtde_nf = mp_info["qtde_nf"].values[0]
            valor_total_nf = mp_info["valor_total_nf"].values[0]
            unidade = mp_info["unidade"].values[0].upper()

            if unidade in ["UNI", "UN"]:  # item unitário
                preco_peca = valor_total_nf / row["produto_qtde"]
                total = valor_total_nf * (row["produto_qtde"] / row["produto_qtde"])
                divergencia = "Produto unitário"
            else:
                if qtde_nf != row["mp_qtde"]:
                    preco_peca = valor_total_nf / row["produto_qtde"]
                    divergencia = "Quantidade MP NF ≠ requisição"
                else:
                    preco_peca = valor_total_nf / row["produto_qtde"]
                    divergencia = "-"
                total = preco_peca * row["produto_qtde"]

        resultados.append({
            "CÓDIGO": row["produto_codigo"],
            "DESCRIÇÃO": row["produto_descricao"],
            "QTDE": row["produto_qtde"],
            "R$/PEÇA": round(preco_peca, 4) if isinstance(preco_peca, float) else preco_peca,
            "TOTAL (R$)": round(total, 2) if isinstance(total, float) else total,
            "DIVERGÊNCIA": divergencia
        })

    return pd.DataFrame(resultados)

# --- Processar ---
if st.button("Gerar Tabela de Custo"):
    try:
        req_df = parse_requisicao(req_text)
        nf_df = parse_nf(nf_text)
        if req_df.empty or nf_df.empty:
            st.error("❌ Não foi possível interpretar a requisição ou a NF. Verifique o texto colado.")
        else:
            resultado_df = calcular_custo(req_df, nf_df)
            st.subheader("Tabela de Custo por Peça")
            st.dataframe(resultado_df)
            st.success("✅ Tabela gerada com base na requisição e NF")
    except Exception as e:
        st.error(f"Erro ao processar: {e}")
