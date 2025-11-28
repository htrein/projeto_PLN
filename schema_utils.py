import sqlite3

def get_schema_from_db(db_path):
    """
    Conecta no banco SQLite e retorna uma string descrevendo as tabelas e colunas.
    Formato de saída esperado pelo LLM:
    Table: nome_tabela, columns: [col1, col2, ...]
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        #Pega todas as tabelas do banco
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        schema_prompt = ""
        
        for table in tables:
            table_name = table[0]
            if table_name == 'sqlite_sequence': 
                continue
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns_info = cursor.fetchall()
            column_names = [col[1] for col in columns_info]
            schema_prompt += f"Table: {table_name}, columns: {column_names}\n"
            
        conn.close()
        return schema_prompt

    except Exception as e:
        return f"Erro ao ler banco de dados: {e}"

if __name__ == "__main__":
    main()