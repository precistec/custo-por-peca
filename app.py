import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Custo por Peça - Precistec", layout="wide")
st.title("Cálculo de Custo por Peça - Precistec")

st.subheader("Cole a Requisição")
req_text = st.text_area("Requisição", height=300)

st.subheader("Cole a Nota Fiscal")
nf_text = st.text_area("Nota Fiscal", height=300)

def parse_requisicao(text):
    produtos = []
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("PRODUTO INTERMEDIÁRIO"):
            # Extrai código, descrição e quantidade no final
            match = re.search(r"(\d+)\s+(.*)\s+(\d+)$", line)
            if match:
                codigo, descricao, qtde_prod = match.groups()
                produto = {
                    "codigo": codigo,
                    "descricao": descricao.strip(),
                    "qtde_prod": int(qtde_prod),
                    "materia_prima": None,
                    "qtde_mp": None
                }
                # Próxima linha deve ser a MP
                if i + 1 < len(lines):
                    mp_line = lines[i+1].strip()
                    if mp_line.startswith("MATÉRIA-PRIMA"):
                        mp_match = re.search(r"(\d+)\s+(.*)\s+([\d.,]+|ALMOXARIFADO|RETALHO)$", mp_line)
                        if mp_match:
                            mp_codigo, mp_desc, mp_qtde = mp_match.groups()
                            mp_qtde = mp_qtde.replace(",", ".")
                            produto["materia_prima"] = mp_codigo
                            if mp_qtde.upper() in ["ALMOXARIFADO", "RETALHO"]:
                                produto["qtde_mp"] = mp_qtde.upper()
                            else:
                                try:
                                    produto["qtde_mp"] = float(mp_qtde)
                                except:
                                    produto["qtde_mp"] = 0.0
                produtos.append(produto)
                i += 2
            else:
                i += 1
        else:
            i += 1
    return produtos

def parse_nf(text):
    nf_items = {}
    lines = text.split("\n")
    for line in lines:
        line = line.strip()
        if not line or line.startswith("CÓDIGO"):
            continue
        parts = re.split(r"\s{2,}|\t", line)
        if len(parts) < 9:
            continue
        codigo = parts[0].strip()
        unidade = parts[5].strip().upper()
        try:
            qtde = float(parts[6].replace(",", "."))
            valor_total = float(parts[8].replace(",", "."))
        except:
            qtde = 0.0
            valor_total = 0.0
        nf_items[codigo] = {
            "unidade": unidade,
            "qtde": qtde,
            "valor_total": valor_total
        }
    return nf_items

def calcular_custo(produtos, nf_items):
    resultados = []
    for p in produtos:
        codigo = p["codigo"]
        qtde_prod = p["qtde_prod"]
        mp = p["materia_prima"]
        qtde_mp = p["qtde_mp"]
        divergencia = ""

        if mp is None:
            rpp = "Não consta na NF"
            divergencia = "MP não informada na requisição"
            total_item = "-"
        elif mp not in nf_items:
            rpp = "Não consta na NF"
            divergencia = "MP não consta na NF"
            total_item = "-"
        elif isinstance(qtde_mp, str) and qtde_mp in ["ALMOXARIFADO", "RETALHO"]:
            rpp = qtde_mp
            divergencia = "Item ALMOXARIFADO ou RETALHO"
            total_item = "-"
        else:
            nf = nf_items[mp]
            if nf["unidade"] in ["UNI", "UN"]:
                # valor total / qtde produto
                rpp = nf["valor_total"] / qtde_prod
                total_item = rpp * qtde_prod
            else:
                qtde_nf = nf["qtde"]
                if qtde_nf != qtde_mp:
                    divergencia = "Quantidade MP NF ≠ requisição"
                rpp = (nf["valor_total"] / qtde_nf) * qtde_mp / qtde_prod
                total_item = rpp * qtde_prod

        resultados.append({
            "CÓDIGO": codigo,
            "DESCRIÇÃO": p["descricao"],
            "QUANTIDADE": qtde_prod,
            "R$/PEÇA": round(rpp,4) if isinstance(rpp,float) else rpp,
            "TOTAL (R$)": round(total_item,2) if isinstance(total_item,float) else total_item,
            "DIVERGÊNCIA": divergencia if divergencia else "—"
        })
    return pd.DataFrame(resultados)

if req_text and nf_text:
    produtos = parse_requisicao(req_text)
    nf_items = parse_nf(nf_text)
    if produtos and nf_items:
        df_result = calcular_custo(produtos, nf_items)
        st.subheader("Tabela Final")
        st.dataframe(df_result)
        total_geral = df_result[df_result['TOTAL (R$)'] != '-']['TOTAL (R$)'].sum()
        st.markdown(f"**TOTAL GERAL (somando coluna TOTAL (R$))**: {total_geral:.2f}")
    else:
        st.error("❌ Não foi possível interpretar a requisição ou a NF. Verifique o texto colado.")
else:
    st.info("Cole a Requisição e a Nota Fiscal acima para processar.")
