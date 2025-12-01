import json
import os
import requests 
import re
from tqdm import tqdm

# --- CONFIGURAÇÕES ---
MODELO = "qwen3:4b" 
ARQUIVO_DADOS = "questions.json"
ARQUIVO_PRED = "pred.txt"
ARQUIVO_GOLD = "gold.txt"

# Limite de execuções para teste (Coloque None para rodar o arquivo todo)
LIMIT = None

# --- CONFIGURAÇÕES DA API REMOTA ---
API_URL = 'https://ollama.k8s.inf.ufrgs.br/ollama/api/chat'
API_TOKEN = ''

def limpar_sql(texto_gerado):
    """
    Tenta extrair apenas o SQL da resposta do modelo.
    Remove blocos de código markdown e quebras de linha.
    """
    # Remove blocos markdown ```sql ... ```
    padrao_markdown = r"```sql\s*(.*?)\s*```"
    match = re.search(padrao_markdown, texto_gerado, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip().replace('\n', ' ')
    
    # Se não houver markdown, tenta pegar o texto cru e remover quebras de linha
    return texto_gerado.replace('\n', ' ').strip()

def chamar_api_remota(prompt, modelo):
    headers = {
        'Authorization': f'Bearer {API_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    data = {
        "model": modelo,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False 
    }

    try:
        response = requests.post(API_URL, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def main():
    print(f"Lendo arquivo de entrada: {ARQUIVO_DADOS}...")
    
    if not os.path.exists(ARQUIVO_DADOS):
        print(f"ERRO: O arquivo {ARQUIVO_DADOS} não foi encontrado.")
        return

    with open(ARQUIVO_DADOS, 'r', encoding='utf-8') as f:
        dados_completos = json.load(f)
    
    lista_questoes = dados_completos.get('questions', [])
    
    # --- APLICAÇÃO DO LIMITE ---
    if LIMIT is not None and isinstance(LIMIT, int):
        print(f"⚠️ MODO DE TESTE ATIVO: Processando apenas os primeiros {LIMIT} itens.")
        lista_questoes = lista_questoes[:LIMIT]
    else:
        print(f"Processando todos os {len(lista_questoes)} itens.")

    with open(ARQUIVO_PRED, 'w', encoding='utf-8') as f_pred, \
         open(ARQUIVO_GOLD, 'w', encoding='utf-8') as f_gold:

        for i, item in tqdm(enumerate(lista_questoes), total=len(lista_questoes), desc="Gerando SQL"):
            try:
                prompt_texto = item['prompt']
                ground_truth = item['response']
                db_id = item.get('db_id', 'unknown')

                json_resposta = chamar_api_remota(prompt_texto, MODELO)
                
                texto_gerado = ""
                if 'message' in json_resposta:
                    texto_gerado = json_resposta['message']['content']
                elif 'response' in json_resposta:
                    texto_gerado = json_resposta['response']
                elif 'error' in json_resposta:
                    tqdm.write(f"Erro API item {i}: {json_resposta['error']}")
                    texto_gerado = "SELECT error FROM model"
                else:
                    texto_gerado = "SELECT error FROM model"
                
                sql_final = limpar_sql(texto_gerado)
                if not sql_final: sql_final = "SELECT * FROM erro_geracao"

                f_pred.write(f"{sql_final}\n")
                f_gold.write(f"{ground_truth}\t{db_id}\n")
                
                f_pred.flush()
                f_gold.flush()
                
            except Exception as e:
                tqdm.write(f"Erro fatal no item {i}: {e}")
                f_pred.write("SELECT error FROM exception\n")
                f_gold.write(f"{item.get('response', 'SELECT error')}\t{item.get('db_id', 'unknown')}\n")

    print("\n✅ Concluído!")

if __name__ == "__main__":
    main()