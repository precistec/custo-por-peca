import re
import pandas as pd

def parse_nf(texto):
    linhas = texto.splitlines()
    dados = []

    for l in linhas:
        l = l.strip()

        if not l or not re.search(r"\b\d{4,6}\b", l):
            continue

        partes = l.split()

        try:
            codigo = partes[0]

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
            continue

    return pd.DataFrame(dados)
