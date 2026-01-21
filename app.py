import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Cálculo de Custo por Peça", layout="wide")

st.title("Cálculo de Custo por Peça — Precistec")

# Campos de texto para colar Requisição e NF
st.subheader("Cole a Requisição")
req_text = st.text_area("Texto da Requisição", height=300)

st.subheader("Cole a Nota Fiscal")
nf_text = st.text_area("Texto da Nota Fiscal", height=300)

# Função para parsear Requisição
def parse_requisicao(texto):
    itens = []
    linhas = texto.strip().split("\n")
    i = 0
    while i < len(linhas):
        linha = linhas[i].strip()
        if linha.startswith("PRODUTO INTERMEDIÁRIO"):
            prod = {
                "tipo": "produto",
                "codigo": linhas[i+1].strip(),
                "descricao": linhas[i+2].strip(),
                "quantidade": float(linhas[i+3].strip().replace(",", ".")),
                "materia_prima": None,
                "consumo": None
            }
            if i+4 < len(linhas) and linhas[i+4].startswith("MATÉRIA-PRIMA"):
                mp = {
                    "codigo": linhas[i+5].strip(),
                    "descricao": linhas[i+6].strip(),
                    "consumo": float(linhas[i+7].strip().replace(",", ".")) if ',' in linhas[i+7] or '.' in linhas[i+7] else float(linhas[i+7].strip())
                }
                prod["materia_prima"] = mp
            itens.append(prod)
            i += 8
        else:
            i += 1
    return itens

# Função para parsear NF
def parse_nf(texto):
    linhas = texto.strip().split("\n")
    nf_itens = []
    for linha in linhas[1:]:  # Pular cabeçalho
        linha = linha.strip()
        if not linha:
            continue
        # Separar campos por espaços, mantendo números com vírgula ou ponto
        partes = re.split(r'\s{2,}', linha)
        if len(partes) < 10:
            continue  # Ignora linhas incompletas
        try:
            nf_itens.append({
                "codigo": partes[0],
                "descricao": partes[1],
                "uni": partes[6],
                "qtde_nf": float(partes[7].replace(",", ".")),
                "valor_unitario": float(partes[8].replace(",", ".")),
                "valor_total": float(partes[9].replace(",", "."))
            })
        except:
            continue
    return nf_itens

# Função para gerar tabela final
def gerar_tabela(req_itens, nf_itens):
    rows = []
    for prod in req_itens:
        mp = prod["materia_prima"]
        if mp:
            # Procurar NF correspondente
            nf_match = [n for n in nf_itens if n["codigo"] == mp["codigo"]]
            if nf_match:
                nf_item = nf_match[0]
                # Se unidade é UNI/UN -> preço por peça = valor unitário
                if nf_item["uni"].upper() in ["UNI", "UN"]:
                    preco_peca = nf_item["valor_unitario"]
                    divergencia = "Item unitário (não entra no rateio)"
                else:
                    # Rateio proporcional
                    preco_peca = (mp["consumo"] * nf_item["valor_unitario"]) / prod["quantidade"]
                    divergencia = ""
            else:
                preco_peca = 0.0
                divergencia = "MP não consta na NF"
        else:
            preco_peca = 0.0
            divergencia = "Sem MP"

        total = preco_peca * prod["quantidade"]
        rows.append({
            "CÓDIGO": prod["codigo"],
            "DESCRIÇÃO": prod["descricao"],
            "QUANTIDADE": prod["quantidade"],
            "R$/PEÇA": round(preco_peca, 4),
            "TOTAL (R$)": round(total, 2),
            "DIVERGÊNCIA": divergencia
        })
    df = pd.DataFrame(rows)
    return df

# Processamento
if st.button("Gerar tabela"):
    if not req_text.strip() or not nf_text.strip():
        st.error("Coloque tanto a Requisição quanto a Nota Fiscal.")
    else:
        try:
            req_itens = parse_requisicao(req_text)
            nf_itens = parse_nf(nf_text)
            if not req_itens or not nf_itens:
                st.error("Não foi possível interpretar a requisição ou a NF. Verifique o texto colado.")
            else:
                tabela_final = gerar_tabela(req_itens, nf_itens)
                st.subheader("Tabela Final")
                st.dataframe(tabela_final)
                st.markdown("✅ Valores prontos para copiar/colar no Word")
        except Exception as e:
            st.error(f"Erro ao processar: {e}")
