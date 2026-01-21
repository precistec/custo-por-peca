import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Custo por Peça - Precistec", layout="wide")

st.title("Cálculo de Custo por Peça - Precistec")
st.markdown("Cole abaixo a Requisição e a Nota Fiscal (texto) para gerar a tabela de custos.")

# --- Campos de texto ---
req_text = st.text_area("Requisição", height=300)
nf_text = st.text_area("Nota Fiscal", height=300)

# --- Funções para parse ---
def parse_requisicao(text):
    """
    Converte o texto da requisição em lista de produtos e MPs
    Funciona para linhas únicas ou padrão antigo
    """
    lines = text.strip().splitlines()
    items = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("PRODUTO INTERMEDIÁRIO") or line.startswith("PRODUTO INTERMEDIÁRIO (PÇ)"):
            # Produto
            produto_codigo = ""
            produto_desc = ""
            produto_qtde = ""
            # Formato compacto: tudo na mesma linha
            m = re.match(r"PRODUTO.*? (\d+) (.+?) (\d+\.?\d*)$", line)
            if m:
                produto_codigo = m.group(1)
                produto_desc = m.group(2)
                produto_qtde = float(m.group(3))
                i += 1
            else:
                # Formato antigo: 4 linhas
                produto_codigo = lines[i+1].strip()
                produto_desc = lines[i+2].strip()
                produto_qtde = float(lines[i+3].strip().replace(",", "."))
                i += 4
            # Próxima linha é MP
            mp_line = lines[i].strip()
            if mp_line.startswith("MATÉRIA-PRIMA") or mp_line.startswith("MATÉRIA-PRIMA (M)"):
                # Formato compacto
                m2 = re.match(r".*? (\d+) (.+?) (\d+\.?\d*)$", mp_line)
                if m2:
                    mp_codigo = m2.group(1)
                    mp_desc = m2.group(2)
                    mp_qtde = float(m2.group(3))
                    i += 1
                else:
                    # Formato antigo: 4 linhas
                    mp_codigo = lines[i+1].strip()
                    mp_desc = lines[i+2].strip()
                    mp_qtde = float(lines[i+3].strip().replace(",", "."))
                    i += 4
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

def parse_nf(text):
    """
    Converte o texto da NF em DataFrame
    Reconhece M, UNI, UN etc
    """
    lines = text.strip().splitlines()
    data = []
    for line in lines:
        line = line.strip()
        if line == "" or line.startswith("CÓDIGO") or line.startswith("---"):
            continue
        parts = re.split(r"\s{2,}", line)
        if len(parts) < 9:
            continue
        codigo = parts[0]
        descricao = parts[1]
        unidade = parts[5]
        qtde = float(parts[6].replace(",", "."))
        vunit = float(parts[7].replace(",", "."))
        valor_total = float(parts[8].replace(",", "."))
        data.append({
            "mp_codigo": codigo,
            "mp_desc": descricao,
            "unidade": unidade,
            "qtde_nf": qtde,
            "vunit_nf": vunit,
            "total_nf": valor_total
        })
    return pd.DataFrame(data)

def calcular_custos(req_df, nf_df):
    """
    Faz o rateio, aplica regras de UNI/UN, cria divergência
    """
    resultado = []
    for idx, row in req_df.iterrows():
        mp_nf = nf_df[nf_df["mp_codigo"] == row["mp_codigo"]]
        divergencia = ""
        preco_peca = 0.0
        if len(mp_nf) == 0:
            preco_peca = 0.0
            divergencia = "Matéria-prima não consta na NF"
        else:
            mp_nf_total = mp_nf["total_nf"].sum()
            if row["mp_qtde"] == 0:
                preco_peca = 0.0
                divergencia = "Quantidade de matéria-prima da requisição diferente da NF"
            else:
                preco_peca = mp_nf_total * (row["mp_qtde"] / mp_nf["qtde_nf"].sum()) / row["produto_qtde"]

            # Verifica unidade
            unidade = mp_nf.iloc[0]["unidade"]
            if unidade.upper() in ["UNI", "UN"]:
                preco_peca = mp_nf_total  # Valor total para itens unitários
                divergencia = f"Produto unitário ({unidade})"
        total = preco_peca * row["produto_qtde"]
        resultado.append({
            "produto_codigo": row["produto_codigo"],
            "produto_desc": row["produto_desc"],
            "produto_qtde": row["produto_qtde"],
            "mp_codigo": row["mp_codigo"],
            "mp_desc": row["mp_desc"],
            "preco_peca": round(preco_peca, 4),
            "total": round(total, 2),
            "divergencia": divergencia
        })
    return pd.DataFrame(resultado)

# --- Processamento ---
if st.button("Calcular custos"):
    try:
        req_df = parse_requisicao(req_text)
        nf_df = parse_nf(nf_text)
        st.subheader("Requisição Estruturada")
        st.dataframe(req_df)
        st.subheader("NF Estruturada")
        st.dataframe(nf_df)
        result_df = calcular_custos(req_df, nf_df)
        st.subheader("Resultado Final")
        st.dataframe(result_df)
        soma_total = result_df["total"].sum()
        st.markdown(f"**Soma total da coluna TOTAL (R$): {soma_total:.2f}**")
    except Exception as e:
        st.error(f"Erro ao processar: {e}")
