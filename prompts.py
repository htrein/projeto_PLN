import json
import os
from schema_utils import get_schema_from_db

def criar_prompt_basico(pergunta, db_id, pasta_bancos='spider_data/database'):
    """
    Constrói o prompt Zero-Shot (apenas schema + pergunta).
    """
    caminho_banco = os.path.join(pasta_bancos, db_id, f"{db_id}.sqlite")

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
    return prompt

if __name__ == "__main__":
    main()