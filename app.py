import streamlit as st
import pandas as pd

st.set_page_config(page_title="Cálculo de Custo por Peça - Precistec", layout="wide")
st.title("Cálculo de Custo por Peça - Precistec")

# --- Inputs ---
st.header("Cole o texto da Requisição")
req_text = st.text_area("Texto da Requisição", height=250)

st.header("Cole o texto da Nota Fiscal")
nf_text = st.text_area("Texto da Nota Fiscal", height=250)

# --- Funções de Parsing ---
def parse_requisicao(text):
    """
    Converte o texto da requisição em DataFrame estruturado.
    Detecta PRODUTO e MP, código, descrição e quantidade.
    """
    lines = text.strip().split("\n")
    dados = []
    current_produto = None
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("PRODUTO INTERMEDIÁRIO"):
            partes = line.split()
            codigo = partes[2]
            descricao = " ".join(partes[3:-1])
            quantidade = partes[-1].replace(",", ".")
            try:
                quantidade = float(quantidade)
            except:
                quantidade = None
            current_produto = {"tipo": "PRODUTO", "codigo": codigo, "descricao": descricao, "qtde": quantidade}
            dados.append(current_produto)
        elif line.startswith("MATÉRIA-PRIMA"):
            partes = line.split()
            codigo = partes[2]
            descricao = " ".join(partes[3:-1])
            quantidade = partes[-1].replace(",", ".")
            try:
                quantidade = float(quantidade)
            except:
                quantidade = None
            mp = {"tipo": "MP", "codigo": codigo, "descricao": descricao, "qtde": quantidade, "produto_vinculado": current_produto["codigo"] if current_produto else None}
            dados.append(mp)
    df = pd.DataFrame(dados)
    return df

def parse_nf(text):
    """
    Converte o texto da NF em DataFrame estruturado.
    """
    lines = text.strip().split("\n")
    dados = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("CÓDIGO"):
            continue
        partes = line.split()
        codigo = partes[0]
        descricao = " ".join(partes[1:-9])
        unidade = partes[-9]
        quantidade = partes[-8].replace(",", ".")
        valor_unitario = partes[-7].replace(",", ".")
        valor_total = partes[-6].replace(",", ".")
        try:
            quantidade = float(quantidade)
            valor_unitario = float(valor_unitario)
            valor_total = float(valor_total)
        except:
            continue
        dados.append({
            "codigo": codigo,
            "descricao": descricao,
            "uni": unidade,
            "qtde_nf": quantidade,
            "v_unit": valor_unitario,
            "v_total": valor_total
        })
    df = pd.DataFrame(dados)
    return df

# --- Processamento ---
if st.button("Processar"):
    try:
        df_req = parse_requisicao(req_text)
        df_nf = parse_nf(nf_text)

        if df_req.empty or df_nf.empty:
            st.error("❌ Não foi possível interpretar a requisição ou a NF. Verifique o texto colado.")
        else:
            st.subheader("Requisição Estruturada")
            st.dataframe(df_req)

            st.subheader("NF Estruturada")
            st.dataframe(df_nf)

            # --- Calculo Preço por Peça ---
            resultado = []
            for idx, row in df_req.iterrows():
                if row["tipo"] == "PRODUTO":
                    continue
                mp_nf = df_nf[df_nf["codigo"] == row["codigo"]]
                if mp_nf.empty:
                    rpp = "Não consta na NF"
                    divergencia = "MP não consta na NF"
                    total = "Não consta na NF"
                else:
                    nf_row = mp_nf.iloc[0]
                    # Se unidade for UNI/UN -> preço por peça = valor unitário
                    if nf_row["uni"].upper() in ["UNI","UN"]:
                        rpp = nf_row["v_unit"]
                        total = nf_row["v_total"]
                        divergencia = "-"
                    else:
                        # Se qtde_nf != qtde requisitada -> rateio
                        if row["qtde"] != nf_row["qtde_nf"]:
                            rpp = nf_row["v_total"] / df_req[df_req["produto_vinculado"]==row["produto_vinculado"]]["qtde"].sum()
                            total = rpp * row["qtde"]
                            divergencia = "Quantidade MP NF ≠ requisição"
                        else:
                            rpp = nf_row["v_total"] / row["qtde"]
                            total = rpp * row["qtde"]
                            divergencia = "-"
                resultado.append({
                    "Código": row["codigo"],
                    "Descrição": row["descricao"],
                    "Qtd": row["qtde"],
                    "R$/Peça": rpp,
                    "Total (R$)": total,
                    "Divergência": divergencia
                })
            df_result = pd.DataFrame(resultado)
            st.subheader("Tabela Final com Preço por Peça")
            st.dataframe(df_result)

    except Exception as e:
        st.error(f"Erro ao processar: {e}")
