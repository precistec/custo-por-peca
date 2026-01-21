import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Cálculo Custo por Peça", layout="wide")

st.title("Cálculo de Custo por Peça - Precistec")
st.markdown("Cole abaixo a **Requisição** e a **Nota Fiscal** nos campos correspondentes.")

# Campos de texto para entrada
req_text = st.text_area("Texto da Requisição", height=300)
nf_text = st.text_area("Texto da Nota Fiscal", height=300)

def parse_requisicao(texto):
    linhas = texto.split("\n")
    produtos = []
    i = 0
    while i < len(linhas):
        linha = linhas[i].strip()
        if not linha:
            i += 1
            continue
        if linha.startswith("PRODUTO INTERMEDIÁRIO") or linha.startswith("PRODUTO INTERMEDIARIO"):
            # Captura código, quantidade e descrição via regex
            match = re.match(r".*?(\d+)\s+(.*?)\s+(\d+)$", linha)
            if not match:
                i += 1
                continue
            codigo = match.group(1)
            descricao = match.group(2)
            qtde = float(match.group(3).replace(",", "."))
            i += 1
            mp_codigo, mp_descricao, mp_qtde = "", "", 0
            if i < len(linhas):
                mp_linha = linhas[i].strip()
                if mp_linha.startswith("MATÉRIA-PRIMA") or mp_linha.startswith("MATERIA-PRIMA"):
                    mp_match = re.match(r".*?(\d+)\s+(.*?)\s+([\d.,]+)$", mp_linha)
                    if mp_match:
                        mp_codigo = mp_match.group(1)
                        mp_descricao = mp_match.group(2)
                        mp_qtde = float(mp_match.group(3).replace(",", "."))
            produtos.append({
                "produto_codigo": codigo,
                "produto_descricao": descricao,
                "produto_qtde": qtde,
                "mp_codigo": mp_codigo,
                "mp_descricao": mp_descricao,
                "mp_qtde": mp_qtde
            })
        i += 1
    return pd.DataFrame(produtos)

def parse_nf(texto):
    linhas = texto.split("\n")
    nf_itens = []
    for linha in linhas:
        linha = linha.strip()
        if not linha or linha.startswith("CÓDIGO") or len(linha) < 5:
            continue
        # Captura último número como valor total
        valor_total_match = re.findall(r"([\d.,]+)\s*$", linha)
        if not valor_total_match:
            continue
        valor_total = float(valor_total_match[-1].replace(",", "."))
        # Captura código, quantidade e unidade
        codigo_match = re.match(r"(\d+)\s+(.*?)\s+(\d+\.?\d*)\s+(\w+)\s*$", linha)
        if codigo_match:
            codigo = codigo_match.group(1)
            descricao = codigo_match.group(2)
            qtde_nf = float(codigo_match.group(3).replace(",", "."))
            unidade = codigo_match.group(4)
        else:
            # fallback mínimo
            partes = linha.split()
            codigo = partes[0]
            descricao = " ".join(partes[1:-2])
            qtde_nf = float(partes[-2].replace(",", "."))
            unidade = partes[-3] if len(partes) > 3 else "M"
        nf_itens.append({
            "codigo": codigo,
            "descricao": descricao,
            "unidade": unidade,
            "qtde_nf": qtde_nf,
            "valor_total_nf": valor_total
        })
    return pd.DataFrame(nf_itens)

def calcular_custo(req_df, nf_df):
    resultados = []
    for idx, row in req_df.iterrows():
        mp_nf = nf_df[nf_df["codigo"] == row["mp_codigo"]]
        if mp_nf.empty:
            preco_peca = "Não consta na NF"
            divergencia = "MP não consta na NF"
        else:
            # Unidade de medida
            if mp_nf.iloc[0]["unidade"].upper() in ["UNI", "UN"]:
                preco_peca = mp_nf["valor_total_nf"].sum() / row["produto_qtde"]
                divergencia = "Produto unitário (UNI/UN)"
            else:
                # Rateio proporcional pelo consumo da requisição
                total_consumo = mp_nf["qtde_nf"].sum()
                if total_consumo == 0:
                    preco_peca = 0
                else:
                    preco_peca = (row["mp_qtde"] / total_consumo) * mp_nf["valor_total_nf"].sum() / row["produto_qtde"]
                divergencia = "-" if row["mp_qtde"] <= total_consumo else "Quantidade MP NF ≠ requisição"
        resultados.append({
            "CÓDIGO": row["produto_codigo"],
            "DESCRIÇÃO": row["produto_descricao"],
            "QTDE": row["produto_qtde"],
            "R$/PEÇA": round(preco_peca, 4) if isinstance(preco_peca, float) else preco_peca,
            "TOTAL (R$)": round(preco_peca * row["produto_qtde"], 2) if isinstance(preco_peca, float) else preco_peca,
            "DIVERGÊNCIA": divergencia
        })
    return pd.DataFrame(resultados)

if st.button("Calcular Custo"):
    try:
        req_df = parse_requisicao(req_text)
        nf_df = parse_nf(nf_text)
        if req_df.empty or nf_df.empty:
            st.error("❌ Não foi possível interpretar a requisição ou a NF. Verifique o texto colado.")
        else:
            result_df = calcular_custo(req_df, nf_df)
            st.subheader("Resultado Final")
            st.dataframe(result_df)
            total_geral = result_df[result_df["TOTAL (R$)"].apply(lambda x: isinstance(x, (int, float)))]["TOTAL (R$)"].sum()
            st.markdown(f"**Total Geral (R$) conferido:** {total_geral:.2f}")
    except Exception as e:
        st.error(f"Erro ao processar: {e}")
