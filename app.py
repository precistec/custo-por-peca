def parse_requisicao(text):
    """
    Converte o texto da requisição em DataFrame
    Funciona para linhas compactas ou separadas
    """
    lines = text.strip().splitlines()
    items = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # Detecta linhas de produto
        if line.startswith("PRODUTO INTERMEDIÁRIO") or line.startswith("PRODUTO INTERMEDIÁRIO (PÇ)"):
            # Captura o código, descrição e quantidade do final da linha usando regex
            m = re.match(r".*? (\d+) (.+) (\d+\.?\d*)$", line)
            if m:
                produto_codigo = m.group(1)
                produto_desc = m.group(2).strip()
                produto_qtde = float(m.group(3))
                i += 1
            else:
                # Não conseguiu parsear, pula linha
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
                    # Linha seguinte não é MP, ignora
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
