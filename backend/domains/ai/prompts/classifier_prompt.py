"""
Template para classificação inteligente de despesas/receitas via IA.
Ainda não utilizado ativamente no pipeline de importação.
"""

CLASSIFIER_PROMPT_V1 = """
Você é um especialista em finanças pessoais.
Classifique o seguinte lançamento bancário em uma das categorias permitidas.
Responda exclusivamente no formato JSON.

Lançamento: {description}
Valor: {amount}
"""
