import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Cálculo de Custo por Peça - Precistec", layout="wide")

st.title("Cálculo de Custo por Peça - Precistec")

st.markdown("""
Cole abaixo o texto da **Requisição** e da **Nota Fiscal** nos campos correspondentes.
""")

req_text = st.text_area("Requisição", height=250)
nf_text = st.text_area("Nota Fiscal", height=250)

def parse_requisicao(texto):
    linhas = texto.strip().split("\n")
    produtos = []
    i = 0
    while i < len(linhas):
        linha = linhas[i].strip()
        if linha.startswith("PRODUTO INTERMEDIÁRIO"):
            partes = linha.split()
            codigo = partes[2]
            descricao = " ".join(partes[3:])
            i += 1
            mp_linha = linhas[i].strip()
            mp_partes = mp_linha.split()
            mp_codigo = mp_partes[2]
            mp_desc = " ".join(mp_partes[3:-1])
            qtde = float(mp_partes[-1].replace(",", "."))
            produtos.append({
                "produto_codigo": codigo,
                "produto_descricao": descricao,
                "mp_codigo": mp_codigo,
                "mp_descricao": mp_desc,
                "qtde_requisicao": qtde
            })
        i += 1
    return pd.DataFrame(produtos)

def parse_nf(texto):
    linhas = texto.strip().split("\n")
    nf = []
    for linha in linhas[1:]:  # Ignora cabeçalho
        partes = re.split(r'\s{2,}', linha.strip())
        if len(partes) < 10:
            continue
        codigo = partes[0]
        descricao = partes[1]
        uni = partes[7]
        qtde = partes[8].replace(",", ".")
        v_unit = partes[9].replace(",", ".")
        total = partes[10].replace(",", ".")
        try:
            qtde = float(qtde)
            v_unit = float(v_unit)
            total = float(total)
        except:
            qtde = v_unit = total = None
        nf.append({
            "mp_codigo": codigo,
            "mp_descricao": descricao,
            "unidade": uni,
            "qtde_nf": qtde,
            "valor_unit_nf": v_unit,
            "valor_total_nf": total
        })
    return pd.DataFrame(nf)

def calcular_precos(req_df, nf_df):
    df = req_df.copy()
    precos = []
    for idx, row in df.iterrows():
        mp_nf = nf_df[nf_df["mp_codigo"] == row["mp_codigo"]]
        if mp_nf.empty:
            precos.append({"preco_por_peca": "Não consta na NF", "total": "Não consta na NF", "divergencia": "MP não consta na NF"})
            continue
        # Unidade em metros
        if mp_nf.iloc[0]["unidade"].upper() != "UNI" and mp_nf.iloc[0]["unidade"].upper() != "UN":
            # Se qtde NF diferente da requisição, usar valor total NF dividido pela qtde da requisição
            qtde_nf_total = mp_nf["qtde_nf"].sum()
            valor_nf_total = mp_nf["valor_total_nf"].sum()
            preco_peca = (valor_nf_total * row["qtde_requisicao"] / qtde_nf_total) / row["qtde_requisicao"]
            total_item = preco_peca * row["qtde_requisicao"]
            divergencia = ""
            if qtde_nf_total != row["qtde_requisicao"]:
                divergencia = "Quantidade MP NF ≠ requisição"
            precos.append({"preco_por_peca": round(preco_peca, 4), "total": round(total_item, 2), "divergencia": divergencia})
        else:
            # Unidade UNI/UN: preço por peça = valor unitário NF
            valor_total = mp_nf["valor_total_nf"].sum()
            precos.append({"preco_por_peca": "-", "total": round(valor_total, 2), "divergencia": "Produto unitário"})
    precos_df = pd.DataFrame(precos)
    resultado = pd.concat([df, precos_df], axis=1)
    return resultado

if st.button("Calcular Preço por Peça"):
    try:
        req_df = parse_requisicao(req_text)
        nf_df = parse_nf(nf_text)
        if req_df.empty or nf_df.empty:
            st.error("❌ Não foi possível interpretar a requisição ou a NF. Verifique o texto colado.")
        else:
            resultado = calcular_precos(req_df, nf_df)
            st.success("✅ Cálculo concluído")
            st.dataframe(resultado)
    except Exception as e:
        st.error(f"❌ Erro ao processar: {e}")
