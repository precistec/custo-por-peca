import re
import pandas as pd
from collections import defaultdict

# ===============================
# 1. CARREGAR DADOS (já extraídos)
# ===============================

# Exemplo: listas vindas do parser de PDF
# Cada item da requisição vem em pares: produto / MP

requisicao = [
    {
        "produto_codigo": "23648",
        "quantidade_pecas": 10,
        "mp_codigo": "14592",
        "mp_consumo_mm": 130
    },
    {
        "produto_codigo": "23649",
        "quantidade_pecas": 4,
        "mp_codigo": "14592",
        "mp_consumo_mm": 320
    },
    # adicione os demais itens
]

# Nota Fiscal (somente MP)
nota_fiscal = {
    "14592": {
        "valor_total": 5.34,
        "quantidade_mm": 130
    },
    # outras MPs
}

# ======================================
# 2. AGRUPAR CONSUMO TOTAL POR MP
# ======================================

consumo_por_mp = defaultdict(int)

for item in requisicao:
    consumo_por_mp[item["mp_codigo"]] += item["mp_consumo_mm"]

# ======================================
# 3. CALCULAR PREÇO POR PEÇA
# ======================================

resultado = []

for item in requisicao:
    prod = item["produto_codigo"]
    mp = item["mp_codigo"]
    qtd_pecas = item["quantidade_pecas"]
    consumo_item = item["mp_consumo_mm"]

    if mp not in nota_fiscal:
        preco_peca = "Não consta na NF"
    else:
        valor_total_mp = nota_fiscal[mp]["valor_total"]
        consumo_total_mp = consumo_por_mp[mp]

        # rateio proporcional
        valor_rateado = (consumo_item / consumo_total_mp) * valor_total_mp
        preco_peca = round(valor_rateado / qtd_pecas, 3)

    resultado.append({
        "Código do Produto": prod,
        "Preço por Peça": preco_peca
    })

# ======================================
# 4. GERAR CSV FINAL (SEM ERROS)
# ======================================

df = pd.DataFrame(resultado)
df.to_csv("export.csv", index=False)

print("Arquivo gerado com sucesso.")
