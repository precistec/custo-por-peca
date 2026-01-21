def parse_nf(texto):
    linhas = texto.splitlines()
    dados = []

    for l in linhas:
        l = l.strip()

        # ignora linhas vazias ou lixo
        if not l or not re.match(r"^\d{4,6}\s", l):
            continue

        partes = l.split()

        try:
            codigo = partes[0]

            # unidade costuma ser o 4º item a partir do fim
            unidade = partes[-4]

            qtde_nf = float(partes[-3].replace(",", "."))
            valor_total = float(partes[-1].replace(",", "."))

            descricao = " ".join(partes[1:-5])

            dados.append({
                "cod_mp": codigo,
                "desc_mp_nf": descricao,
                "unidade": unidade,
                "qtde_nf": qtde_nf,
                "valor_total": valor_total
            })

        except Exception:
            # se alguma linha vier quebrada, simplesmente ignora
            continue

    return pd.DataFrame(dados)
