import streamlit as st

st.set_page_config(page_title="Precistec | Custo NF x Requisição", layout="wide")

st.title("📊 Precistec – Conferência de Custo por Peça")
st.markdown("Cole a **Nota Fiscal** e a **Requisição** abaixo. O sistema irá cruzar os dados conforme as regras da Precistec.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📄 Nota Fiscal (cole aqui)")
    nf_texto = st.text_area(
        "NF",
        height=350,
        placeholder="Cole aqui a Nota Fiscal exatamente como vem do sistema"
    )

with col2:
    st.subheader("📋 Requisição (cole aqui)")
    req_texto = st.text_area(
        "Requisição",
        height=350,
        placeholder="Cole aqui a Requisição exatamente como vem do sistema"
    )

st.divider()

if st.button("🔍 Processar NF x Requisição"):
    if not nf_texto or not req_texto:
        st.warning("⚠️ Cole a Nota Fiscal e a Requisição antes de processar.")
    else:
        st.success("✔️ Textos recebidos com sucesso!")
        st.info("🚧 Próximo passo: interpretar, cruzar e aplicar todas as regras Precistec automaticamente.")
