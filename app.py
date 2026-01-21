import streamlit as st
import pandas as pd

st.set_page_config(page_title="Cálculo de Custo por Peça - Precistec", layout="wide")
st.title("Cálculo de Custo por Peça — Precistec")

st.markdown("""
Cole abaixo o texto da **Requisição** e da **Nota Fiscal**.
O sistema vai gerar a tabela de preço por peça com divergências destacadas.
""")

req_text = st.text_area("Requisição", height=300)
nf_text = st.text_area("Nota Fiscal", height=300)

# ------------------ FUNÇÕES ------------------

def parse_requisicao(text):
    linhas = text.strip().splitlines()
    itens = []
    produto_atual = None
    for linha in linhas:
        linha = linha.strip()
        if linha.startswith("PRODUTO INTERMEDIÁRIO"):
            partes = linha.split()
            codigo = partes[2]
            qtde = float(partes[-1].replace(",", "."))
            descricao = " ".join(partes[3:-1])
            produto_atual = {"codigo_prod": codigo, "descricao_prod": descricao, "qtde_prod": qtde}
        elif linha.startswith("MATÉRIA-PRIMA"):
            partes = linha.split()
            codigo_mp = partes[2]
            qtde_mp = float(partes[-1].replace(",", "."))
            descricao_mp = " ".join(partes[3:-1])
            if produto_atual:
                produto_atual.update({
                    "codigo_mp": codigo_mp,
                    "descricao_mp": descricao_mp,
                    "qtde_mp": qtde_mp
                })
                itens.append(produto_atual)
                produto_atual = None
    return pd.DataFrame(itens)

def parse_nf(text):
    linhas = text.strip().splitlines()
    nf_itens = []
    for linha in linhas[1:]:
        linha = linha.strip()
        if not linha:
            continue
        partes = linha.split()
        if len(partes) < 7:
            continue
        codigo = partes[0]
        # Detecta a quantidade
        for i, p in enumerate(partes[1:], start=1):
            try:
                float(p.replace(",", "."))
                idx_qtde = i
                break
            except:
                continue
        descricao = " ".join(partes[1:idx_qtde])
        uni = partes[idx_qtde - 1]
        qtde = float(partes[idx_qtde].replace(",", "."))
        v_unit = float(partes[idx_qtde+1].replace(",", "."))
        v_total = float(partes[idx_qtde+2].replace(",", "."))
        nf_itens.append({
            "codigo_mp": codigo,
            "descricao_mp": descricao,
            "uni": uni,
            "qtde_nf": qtde,
            "v_unit_nf": v_unit,
            "v_total_nf": v_total
        })
    return pd.DataFrame(nf_itens)

def calcular_preco_por_peca(req_df, nf_df):
    resultados = []
    for _, row in req_df.iterrows():
        mp_nf = nf_df[nf_df["codigo_mp"] == row["codigo_mp"]]

        if mp_nf.empty:
            resultados.append({
                "codigo_prod": row["codigo_prod"],
                "descricao_prod": row["descricao_prod"],
                "qtde_prod": row["qtde_prod"],
                "preco_peca": "Não consta na NF",
                "total": "Não consta na NF",
                "divergencia": "MP não consta na NF"
            })
            continue

        # Itens unitários
        if mp_nf["uni"].iloc[0].upper() in ["UNI","UN"]:
            total_unit = mp_nf["v_total_nf"].sum()
            resultados.append({
                "codigo_prod": row["codigo_prod"],
                "descricao_prod": row["descricao_prod"],
                "qtde_prod": row["qtde_prod"],
                "preco_peca": "—",
                "total": total_unit,
                "divergencia": "-"
            })
            continue

        # Rateio proporcional
        valor_total_nf = mp_nf["v_total_nf"].sum()
        qtde_total_req = row["qtde_mp"]
        preco_peca = valor_total_nf / row["qtde_prod"]
        total = preco_peca * row["qtde_prod"]

        # Divergência
        qtde_nf_total = mp_nf["qtde_nf"].sum()
        if qtde_nf_total != row["qtde_mp"]:
            divergencia = "Quantidade MP NF ≠ requisição"
        else:
            divergencia = "-"

        resultados.append({
            "codigo_prod": row["codigo_prod"],
            "descricao_prod": row["descricao_prod"],
            "qtde_prod": row["qtde_prod"],
            "preco_peca": round(preco_peca, 4),
            "total": round(total, 2),
            "divergencia": divergencia
        })

    return pd.DataFrame(resultados)

# ------------------ BOTÃO ------------------

if st.button("Gerar Tabela"):
    try:
        req_df = parse_requisicao(req_text)
        nf_df = parse_nf(nf_text)

        if req_df.empty or nf_df.empty:
            st.error("❌ Não foi possível interpretar a requisição ou a NF. Verifique o texto colado.")
        else:
            tabela = calcular_preco_por_peca(req_df, nf_df)
            st.dataframe(tabela)
            total_geral = tabela[tabela["total"].apply(lambda x: isinstance(x, (int,float)))].total.sum()
            st.markdown(f"**Total Geral (excluindo itens unitários):** R$ {total_geral:.2f}")
            st.markdown("✅ Tabela gerada com base nas regras da Precistec.")

    except Exception as e:
        st.error(f"Erro ao processar: {e}")
