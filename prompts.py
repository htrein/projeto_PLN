import os
from schema_utils import get_schema_from_db


def criar_prompt_few_shot(pergunta, db_id, exemplos=None, pasta_bancos='spider_data/database'):
    """Gera o prompt inicial (Agente Gerador)"""
    caminho_banco = os.path.join(pasta_bancos, db_id, f"{db_id}.sqlite")
    if not os.path.exists(caminho_banco):  # Fallback para estrutura duplicada
        caminho_banco = os.path.join(pasta_bancos, 'spider_data', 'database', db_id, f"{db_id}.sqlite")

    schema = get_schema_from_db(caminho_banco)

    prompt = f"""You are a SQL expert. Generate a SQLite query for the question.
Schema:
{schema}

"""
    if exemplos is None:
        exemplos = []

    for ex in exemplos:
        prompt += f"Question: {ex.get('question','')}\nSQL: {ex.get('query','')}\n\n"

    prompt += f"Question: {pergunta}\n"
    prompt += "Instruction: Output the SQL query inside a markdown block like ```sql\nSELECT ...\n```."
    return prompt

def criar_prompt_corretor(pergunta, db_id, sql_errado, erro_msg, pasta_bancos='spider_data/database'):
    """Gera o prompt de correção (Agente Corretor)"""
    caminho_banco = os.path.join(pasta_bancos, db_id, f"{db_id}.sqlite")
    if not os.path.exists(caminho_banco):
        caminho_banco = os.path.join(pasta_bancos, 'spider_data', 'database', db_id, f"{db_id}.sqlite")

    schema = get_schema_from_db(caminho_banco)

    return f"""You are a SQL debugging expert. The following query failed to execute.

Schema:
{schema}

Question: {pergunta}
Invalid SQL: {sql_errado}
Error Message: {erro_msg}

Task: Fix the SQL query to resolve the error.
Instruction: Output the corrected SQL inside a markdown block like ```sql\nSELECT ...\n```.
Output ONLY the SQL (no explanations)."""

def criar_prompt_basico(pergunta, db_id, pasta_bancos='spider_data/database'):
    """
    Constrói o prompt Zero-Shot (apenas schema + pergunta).
    """
    caminho_banco = os.path.join(pasta_bancos, db_id, f"{db_id}.sqlite")
    if not os.path.exists(caminho_banco):
        caminho_banco = os.path.join(pasta_bancos, 'spider_data', 'database', db_id, f"{db_id}.sqlite")

    schema_text = get_schema_from_db(caminho_banco)

    # definir estrutura
    prompt = f"""### Instruction:
Your task is to generate a valid SQLite SQL query to answer the following question.

### Database Schema:
{schema_text}

### Question:
{pergunta}

### SQL Query:
"""
    # reforçar formato de saída
    prompt += "Instruction: Output the SQL query inside a markdown block like ```sql\nSELECT ...\n```."
    return prompt

def criar_prompt_zeroshot(question, db_id, schema_text):
    return f"""
You are a professional SQL generator for the Spider benchmark.

Database ID: {db_id}

Schema:
{schema_text}

Your task: Write ONLY the SQL query that answers the question below.
Do NOT add explanations.
Do NOT add markdown.
Do NOT add comments.

Question: {question}

SQL:
"""
