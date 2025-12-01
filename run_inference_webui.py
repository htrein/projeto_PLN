import json
import os
import requests 
import re
from tqdm import tqdm
from prompts import criar_prompt_basico

# --- CONFIGURAÇÕES ---
MODELO = "qwen3:4b" 
PASTA_DADOS = "spider_data"
MAX_EXEMPLOS = 10

# --- CONFIGURAÇÕES DA API REMOTA ---
API_URL = 'https://ollama.k8s.inf.ufrgs.br/ollama/api/chat'
API_TOKEN = ''

def limpar_sql(texto_gerado):
    """
    Tenta extrair apenas o SQL da resposta do modelo.
    """
    padrao_markdown = r"```sql\s*(.*?)\s*```"
    match = re.search(padrao_markdown, texto_gerado, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    return texto_gerado.replace('\n', ' ').strip()

def chamar_api_remota(prompt, modelo):
    """
    Função adaptada para usar requests com o payload especificado.
    """
    headers = {
        'Authorization': f'Bearer {API_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    # Payload for /api/chat
    data = {
        "model": modelo,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": False  
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=data)
        response.raise_for_status() # Levanta erro se não for 200 OK
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"\nErro de conexão com API: {e}")
        return None

def main():
    print(f"Iniciando inferência via API Remota com modelo: {MODELO}")
    
    caminho_dev = os.path.join(PASTA_DADOS, 'dev.json')
    caminho_db = os.path.join(PASTA_DADOS, 'database')
    
    if not os.path.exists(caminho_db):
        caminho_db_alternativo = os.path.join(PASTA_DADOS, 'spider_data', 'database')
        if os.path.exists(caminho_db_alternativo):
            caminho_db = caminho_db_alternativo
            print(f"Aviso: Usando caminho alternativo para bancos: {caminho_db}")

    try:
        with open(caminho_dev, 'r') as f:
            dataset = json.load(f)
    except FileNotFoundError:
        print(f"❌ Erro: Não encontrei {caminho_dev}. Verifique o nome da pasta.")
        return

    amostra = dataset[:MAX_EXEMPLOS] if MAX_EXEMPLOS else dataset
    
    print(f"Processando {len(amostra)} exemplos...")

    with open('pred.txt', 'w') as f_pred, open('gold.txt', 'w') as f_gold:
        
        # Wrapped in enumerate to show item numbers in logs
        for i, item in enumerate(tqdm(amostra)):
            try:
                # 1. Gera o Prompt
                prompt = criar_prompt_basico(item['question'], item['db_id'], pasta_bancos=caminho_db)
                
                # 2. Chama a API Remota
                json_resposta = chamar_api_remota(prompt, MODELO)
                
                texto_gerado = ""
                if json_resposta:
                    # --- EXTRACTION OF SERVER TIMINGS ---
                    # Ollama returns durations in nanoseconds. Divide by 1e9 to get seconds.
                    server_total  = json_resposta.get('total_duration', 0) / 1e9
                    server_load   = json_resposta.get('load_duration', 0) / 1e9
                    server_prompt = json_resposta.get('prompt_eval_duration', 0) / 1e9
                    server_gen    = json_resposta.get('eval_duration', 0) / 1e9
                    
                    # Print without breaking the progress bar
                    tqdm.write(
                        f"Item {i+1} [Server Times]: "
                        f"Total={server_total:.2f}s | "
                        f"Load={server_load:.2f}s | "
                        f"Prompt={server_prompt:.2f}s | "
                        f"Gen={server_gen:.2f}s"
                    )

                    # Extract Content
                    if 'message' in json_resposta:
                        texto_gerado = json_resposta['message']['content']
                    elif 'response' in json_resposta:
                        texto_gerado = json_resposta['response']
                    else:
                        tqdm.write(f"Formato de resposta desconhecido: {json_resposta.keys()}")
                
                # 3. Limpa a resposta
                sql_final = limpar_sql(texto_gerado)
                
                if not sql_final: 
                    sql_final = "SELECT * FROM erro_geracao"

                # 4. Salva
                f_pred.write(f"{sql_final}\n")
                f_gold.write(f"{item['query']}\t{item['db_id']}\n")
                
            except Exception as e:
                tqdm.write(f"Erro no item {item['question']}: {e}")
                f_pred.write("SELECT error FROM model\n")
                f_gold.write(f"{item['query']}\t{item['db_id']}\n")

    print("\n✅ Concluído!")
    print("Arquivos gerados: 'pred.txt' (IA) e 'gold.txt' (Gabarito)")

if __name__ == "__main__":
    main()