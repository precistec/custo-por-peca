import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Custo por Peça", layout="wide")
st.title("Cálculo de Custo por Peça - Precistec")

# -------------------------
# Função para parsear requisição
# -------------------------
def parse_requisicao(text):
    lines = text.strip().splitlines()
    items = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # Detecta linhas de produto
        if line.startswith("PRODUTO INTERMEDIÁRIO") or line.startswith("PRODUTO INTERMEDIÁRIO (PÇ)"):
            m = re.match(r".*? (\d+) (.+) (\d+\.?\d*)$", line)
            if m:
                produto_codigo = m.group(1)
                produto_desc = m.group(2).strip()
                produto_qtde = float(m.group(3))
                i += 1
            else:
                i += 1
                continue

            # Próxima linha é MP
            if i < len(lines):
                mp_line = lines[i].strip()
                if mp_line.startswith("MATÉRIA-PRIMA"):
                    m2 = re.match(r".*? (\d+) (.+) (\d+\.?\d*)$", mp_line)
                    if m2:
                        mp_codigo = m2.group(1)
                        mp_desc = m2.group(2).strip()
                        mp_qtde = float(m2.group(3))
                        i += 1
                    else:
                        i += 1
                        continue
                else:
                    i += 1
                    continue

            items.append({
                "produto_codigo": produto_codigo,
                "produto_desc": produto_desc,
                "produto_qtde": produto_qtde,
                "mp_codigo": mp_codigo,
                "mp_desc": mp_desc,
                "mp_qtde": mp_qtde
            })
        else:
            i += 1
    return pd.DataFrame(items)

# -------------------------
# Função para parsear NF
# -------------------------
def parse_nf(text):
    lines = text.strip().splitlines()
    nf_items = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("CÓDIGO"):
            continue
        partes = re.split(r"\s{2,}", line)
        if len(partes) < 8:
            continue
        try:
            nf_items.append({
                "codigo": partes[0],
                "descricao": partes[1],
                "uni": partes[4],
                "qtde_nf": float(partes[5].replace(",", ".")),
                "valor_unitario": float(partes[6].replace(",", ".")),
                "valor_total": float(partes[7].replace(",", ".")),
            })
        except:
            st.warning(f"Não foi possível parsear linha da NF: {line}")
    return pd.DataFrame(nf_items)

# -------------------------
# Entrada de dados
# -------------------------
st.subheader("Cole aqui a Requisição")
req_text = st.text_area("Requisição", height=300)

st.subheader("Cole aqui a Nota Fiscal")
nf_text = st.text_area("Nota Fiscal", height=300)

if st.button("Processar"):
    if not req_text or not nf_text:
        st.warning("Preencha ambos os campos")
    else:
        # Parse
        try:
            req_df = parse_requisicao(req_text)
            nf_df = parse_nf(nf_text)
        except Exception as e:
            st.error(f"Erro ao processar: {e}")
            st.stop()

        if req_df.empty or nf_df.empty:
            st.error("Não foi possível interpretar a requisição ou a NF. Verifique o texto colado.")
            st.stop()

        st.subheader("Requisição Estruturada")
        st.dataframe(req_df)

        st.subheader("NF Estruturada")
        st.dataframe(nf_df)

        # -------------------------
        # Cálculo preço por peça
        # -------------------------
        def calcular_preco_peca(req_df, nf_df):
            resultado = []
            for _, row in req_df.iterrows():
                mp_nf = nf_df[nf_df['codigo'] == row['mp_codigo']]
                if mp_nf.empty:
                    preco_peca = "Não consta na NF"
                    divergencia = "MP não consta na NF"
                else:
                    # Unidade em UNI/UN não faz rateio
                    if any(x in mp_nf['uni'].iloc[0].upper() for x in ["UNI", "UN"]):
                        preco_peca = mp_nf['valor_total'].sum() / row['produto_qtde']
                        divergencia = "Item unitário, valor total usado"
                    else:
                        # Rateio proporcional
                        total_mp_nf = mp_nf['valor_total'].sum()
                        total_consumo_req = req_df[req_df['mp_codigo'] == row['mp_codigo']]['mp_qtde'].sum()
                        proporcao = row['mp_qtde'] / total_consumo_req if total_consumo_req else 0
                        preco_peca = round(proporcao * total_mp_nf / row['produto_qtde'], 4)
                        divergencia = "" if total_mp_nf == total_mp_nf else "Quantidade de MP da requisição diferente da NF"
                resultado.append({
                    "CÓDIGO": row['produto_codigo'],
                    "DESCRIÇÃO": row['produto_desc'],
                    "QTDE": row['produto_qtde'],
                    "R$/PEÇA": preco_peca,
                    "TOTAL (R$)": round(preco_peca * row['produto_qtde'], 2) if isinstance(preco_peca, float) else preco_peca,
                    "DIVERGÊNCIA": divergencia
                })
            return pd.DataFrame(resultado)

        final_df = calcular_preco_peca(req_df, nf_df)

        st.subheader("Resultado Final")
        st.dataframe(final_df)

        total_geral = final_df[final_df['TOTAL (R$)'].apply(lambda x: isinstance(x, float))]['TOTAL (R$)'].sum()
        st.markdown(f"**Total Geral (somando apenas valores numéricos): R$ {total_geral:.2f}**")
