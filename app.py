def parse_nf(texto):
    linhas = texto.splitlines()
    dados = []

    st.subheader("DEBUG — Processando linhas da NF")

    for i, l in enumerate(linhas):
        original = l
        l = l.strip()

        if not l:
            st.write(f"Linha {i}: vazia → IGNORADA")
            continue

        if not re.search(r"\d", l):
            st.write(f"Linha {i}: sem números → IGNORADA → {original}")
            continue

        st.write(f"Linha {i}: ANALISADA → {original}")

        partes = l.split()

        try:
            codigo = partes[0]

            qtde = partes[-3].replace(",", ".")
            total = partes[-1].replace(",", ".")

            qtde_nf = float(qtde)
            valor_total = float(total)

            unidade = partes[-4]
            descricao = " ".join(partes[1:-5])

            dados.append({
                "cod_mp": codigo,
                "desc_mp_nf": descricao,
                "unidade": unidade,
                "qtde_nf": qtde_nf,
                "valor_total": valor_total
            })

            st.write(f"✔ Linha {i} OK → código {codigo}")

        except Exception as e:
            st.write(f"❌ Linha {i} ERRO → {original}")
            st.write(e)

    st.write(f"TOTAL DE ITENS EXTRAÍDOS: {len(dados)}")
    return pd.DataFrame(dados)
