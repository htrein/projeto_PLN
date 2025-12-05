import json
import os
import ollama
import sqlite3
import re
import random
from tqdm import tqdm
from prompts import criar_prompt_few_shot, criar_prompt_corretor

# --- CONFIGURAÇÃO ---
MODELO = "mistral"
PASTA_DADOS = "spider_data"
MAX_EXEMPLOS = None # Coloque None para rodar tudo, ou 10 para teste rápido.

def validar_sql(sql, db_path):
    if not os.path.exists(db_path): return False, "Database not found"
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)

def limpar_sql_blindado(texto):
    """
    Função de limpeza agressiva.
    Remove markdown, explicações e LIXO de objetos Python vazados.
    """
    if not texto: return "SELECT * FROM error"
    
    # 1. Se tiver blocos de código ```sql ... ```, pega o que tem dentro
    match_md = re.search(r"```(?:sql)?\s*(SELECT.*?)```", texto, re.IGNORECASE | re.DOTALL)
    if match_md:
        texto = match_md.group(1)
    
    # 2. Remove qualquer coisa que pareça tupla Python ('thinking', None)
    texto = re.sub(r"\('thinking',.*", "", texto) 
    
    # 3. Pega apenas do SELECT até o primeiro ponto e virgula
    match_select = re.search(r"(SELECT\s.*?;)", texto, re.IGNORECASE | re.DOTALL)
    if match_select:
        texto = match_select.group(1)
    else:
        # Se não achou ponto e virgula, tenta pegar até o fim da linha ou string
        match_select_no_semi = re.search(r"(SELECT\s.*)", texto, re.IGNORECASE | re.DOTALL)
        if match_select_no_semi:
            texto = match_select_no_semi.group(1)

    # 4. Limpeza final de espaços e crases
    texto = texto.replace("`", "").replace(";", "").strip()
    
    return texto

def main():
    print(f"🚀 Iniciando Pipeline Final na RTX 5060 ({MODELO})")
    
    try:
        with open(os.path.join(PASTA_DADOS, 'dev.json'), 'r') as f:
            dev_data = json.load(f)
        with open(os.path.join(PASTA_DADOS, 'train_spider.json'), 'r') as f:
            train_data = json.load(f)
    except:
        print("❌ Erro: Verifique se a pasta spider_data está correta.")
        return

    amostra = dev_data[:MAX_EXEMPLOS] if MAX_EXEMPLOS else dev_data
    
    f_pred = open('pred.txt', 'w')
    f_gold = open('gold.txt', 'w')
    
    stats = {"sucesso": 0, "corrigido": 0, "falha": 0}

    for item in tqdm(amostra, desc="Processando"):
        db_id = item['db_id']
        db_path = os.path.join(PASTA_DADOS, 'database', db_id, f"{db_id}.sqlite")
        if not os.path.exists(db_path):
             db_path = os.path.join(PASTA_DADOS, 'spider_data', 'database', db_id, f"{db_id}.sqlite")

        # 1. Gera (Few-Shot 3 exemplos)
        exemplos = random.sample(train_data, 3)
        prompt_gen = criar_prompt_few_shot(item['question'], db_id, exemplos)
        
        res = ollama.generate(model=MODELO, prompt=prompt_gen)
        # PEGA APENAS A STRING 'response'
        sql_atual = limpar_sql_blindado(res.get('response', ''))

        # 2. Valida e Corrige
        sucesso, erro = validar_sql(sql_atual, db_path)
        
        if sucesso:
            stats["sucesso"] += 1
        else:
            # Tenta corrigir
            prompt_fix = criar_prompt_corretor(item['question'], db_id, sql_atual, erro)
            res_fix = ollama.generate(model=MODELO, prompt=prompt_fix)
            sql_corrigido = limpar_sql_blindado(res_fix.get('response', ''))
            
            sucesso_fix, _ = validar_sql(sql_corrigido, db_path)
            if sucesso_fix:
                stats["corrigido"] += 1
                sql_atual = sql_corrigido
            else:
                stats["falha"] += 1

        # Salva
        f_pred.write(f"{sql_atual}\n")
        f_gold.write(f"{item['query']}\t{db_id}\n")
        f_pred.flush()

    f_pred.close()
    f_gold.close()
    print(f"\n📊 Resultado: {stats}")
    print("Agora rode o evaluation.py --etype exec")

if __name__ == "__main__":
    main()