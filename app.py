import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Cálculo Custo por Peça - Precistec", layout="wide")
st.title("💻 Cálculo de Custo por Peça - Precistec")

# -----------------------
# Função para processar Requisição
# -----------------------
def parse_requisicao(texto):
    linhas = texto.strip().splitlines()
    produtos = []
    i = 0
    while i < len(linhas):
        linha = linhas[i].strip()
        # Produto
        if "PRODUTO INTERMEDIÁRIO" in linha:
            match_prod = re.match(r".*?(\d+)\s+(.*)\s+(\d+)$", linha)
            if match_prod:
                codigo, descricao, qtde = match_prod.groups()
                qtde = float(qtde.replace(",", "."))
                i += 1
                if i < len(linhas):
                    linha_mp = linhas[i].strip()
                    match_mp = re.match(r".*?(\d+)\s+(.*)\s+([\d,.]+|RETALHO|ALMOXARIFADO)$", linha_mp)
                    if match_mp:
                        mp_codigo, mp_descricao, mp_qtde = match_mp.groups()
                        if mp_qtde.upper() in ["RETALHO", "ALMOXARIFADO"]:
                            mp_qtde_valor = mp_qtde.upper()
                        else:
                            mp_qtde_valor = float(mp_qtde.replace(",", "."))
                        produtos.append({
                            "produto_codigo": codigo,
                            "produto_descricao": descricao,
                            "produto_qtde": qtde,
                            "mp_codigo": mp_codigo,
                            "mp_descricao": mp_descricao,
                            "mp_qtde": mp_qtde_valor
                        })
        i += 1
    return pd.DataFrame(produtos)

# -----------------------
# Função para processar NF
# -----------------------
def parse_nf(texto):
    linhas = texto.strip().splitlines()
    nf = []
    for linha in linhas:
        linha = linha.strip()
        if linha == "" or "CÓDIGO" in linha:
            continue
        # Captura dados do item da NF
        match_nf = re.match(
            r"(\d+)\s+(.*?)\s+(\d+\.?\d*|\d*,\d+|UNI|UN)\s+(\d+[\d,.]*)\s+([\d,.]+)\s+([\d,.]+)",
            linha)
        if match_nf:
            codigo, descricao, uni, qtde, v_unit, valor_total = match_nf.groups()
            # Converte para float quando aplicável
            try:
                qtde_val = float(qtde.replace(",", "."))
            except:
                qtde_val = qtde  # UNI/UN
            v_unit_val = float(v_unit.replace(",", "."))
            valor_total_val = float(valor_total.replace(",", "."))
            nf.append({
                "mp_codigo": codigo,
                "mp_descricao": descricao,
                "mp_unidade": uni,
                "mp_qtde": qtde_val,
                "mp_valor_unit": v_unit_val,
                "mp_valor_total": valor_total_val
            })
    return pd.DataFrame(nf)

# -----------------------
# Função de cálculo de preço por peça
# -----------------------
def calcular_precos(df_req, df_nf):
    resultado = []
    for _, row in df_req.iterrows():
        mp_nf = df_nf[df_nf["mp_codigo"] == row["mp_codigo"]]
        if len(mp_nf) == 0:
            preco = "Não consta na NF"
            divergencia = "MP não consta na NF"
        else:
            mp_nf = mp_nf.iloc[0]
            if isinstance(row["mp_qtde"], str):  # RETALHO ou ALMOXARIFADO
                preco = row["mp_qtde"]
                divergencia = "-"
            else:
                if isinstance(mp_nf["mp_qtde"], float):
                    preco = (mp_nf["mp_valor_total"] / row["produto_qtde"])
                    divergencia = "-" if mp_nf["mp_qtde"] == row["mp_qtde"] else "Quantidade MP NF ≠ requisição"
                else:  # unidade
                    preco = mp_nf["mp_valor_unit"]
                    divergencia = "Produto unitário (UNI/UN)"
        total = preco * row["produto_qtde"] if isinstance(preco, (float,int)) else "-"
        resultado.append({
            "CÓDIGO": row["produto_codigo"],
            "DESCRIÇÃO": row["produto_descricao"],
            "QTDE": row["produto_qtde"],
            "R$/PEÇA": round(preco,4) if isinstance(preco,(float,int)) else preco,
            "TOTAL (R$)": round(total,2) if isinstance(total,(float,int)) else total,
            "DIVERGÊNCIA": divergencia
        })
    return pd.DataFrame(resultado)

# -----------------------
# Layout Streamlit
# -----------------------
st.markdown("### 📝 Cole aqui a Requisição:")
req_text = st.text_area("Requisição", height=300)

st.markdown("### 📄 Cole aqui a Nota Fiscal:")
nf_text = st.text_area("Nota Fiscal", height=300)

if st.button("Calcular Preço por Peça"):
    try:
        df_req = parse_requisicao(req_text)
        df_nf = parse_nf(nf_text)
        if df_req.empty or df_nf.empty:
            st.error("❌ Não foi possível interpretar a requisição ou a NF. Verifique o texto colado.")
        else:
            st.success("✅ Requisição e NF interpretadas com sucesso!")
            df_result = calcular_precos(df_req, df_nf)
            st.dataframe(df_result)
            # Mostra soma total
            total_geral = df_result[df_result["TOTAL (R$)"].apply(lambda x: isinstance(x,(float,int)))].sum()["TOTAL (R$)"]
            st.markdown(f"**💰 Soma TOTAL (considerando apenas valores numéricos): {total_geral:.2f}**")
    except Exception as e:
        st.error(f"Erro ao processar: {e}")
