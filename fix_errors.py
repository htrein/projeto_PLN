import json
import os
import requests 
import re
import time
from tqdm import tqdm

# --- CONFIGURAÇÕES ---
ARQUIVO_JSON = "questions.json"
ARQUIVO_PRED_ORIGINAL = "pred.txt"
ARQUIVO_PRED_FIXED = "pred_fixed.txt" # Salva num novo arquivo para segurança

MODELO = "qwen3:4b"
API_URL = 'https://ollama.k8s.inf.ufrgs.br/ollama/api/chat'
API_TOKEN = 'sk-bc09204ddb8c4fce90cc99965631e188'

# Marcador de erro que seu script original salvou
MARCADOR_ERRO = "SELECT error FROM"

def chamar_api_com_retry(prompt):
    headers = {'Authorization': f'Bearer {API_TOKEN}', 'Content-Type': 'application/json'}
    data = {"model": MODELO, "messages": [{"role": "user", "content": prompt}], "stream": False}
    
    # Tenta até 3 vezes se der timeout
    for attempt in range(3):
        try:
            response = requests.post(API_URL, headers=headers, json=data, timeout=120)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            time.sleep(5) # Espera 5s antes de tentar de novo
            if attempt == 2: return {"error": str(e)}

def limpar_sql(texto_gerado):
    padrao_markdown = r"```sql\s*(.*?)\s*```"
    match = re.search(padrao_markdown, texto_gerado, re.DOTALL | re.IGNORECASE)
    if match: return match.group(1).strip().replace('\n', ' ')
    return texto_gerado.replace('\n', ' ').strip()

def main():
    print("Iniciando correção de falhas...")

    # 1. Carregar dados originais
    with open(ARQUIVO_JSON, 'r', encoding='utf-8') as f:
        questoes = json.load(f)['questions']

    with open(ARQUIVO_PRED_ORIGINAL, 'r', encoding='utf-8') as f:
        linhas_pred = f.readlines()

    # Verifica integridade básica
    if len(linhas_pred) > len(questoes):
        print(f"⚠️ Aviso: pred.txt tem mais linhas ({len(linhas_pred)}) que o json ({len(questoes)}). Verifique.")
    
    # Lista para armazenar as correções
    novas_linhas = [linha.strip() for linha in linhas_pred]
    indices_para_corrigir = [i for i, linha in enumerate(novas_linhas) if MARCADOR_ERRO in linha]

    print(f"Encontrados {len(indices_para_corrigir)} erros para corrigir.")

    # 2. Loop apenas nos erros
    for idx in tqdm(indices_para_corrigir, desc="Reparando"):
        item = questoes[idx]
        prompt = item['prompt']
        
        # Chama API
        resp = chamar_api_com_retry(prompt)
        
        texto = ""
        if 'message' in resp: texto = resp['message']['content']
        elif 'response' in resp: texto = resp['response']
        else: texto = "SELECT error FROM retry_failed"
        
        sql_limpo = limpar_sql(texto)
        if not sql_limpo: sql_limpo = "SELECT error FROM retry_empty"
        
        # Atualiza a lista na memória
        novas_linhas[idx] = sql_limpo

    # 3. Salvar arquivo corrigido
    with open(ARQUIVO_PRED_FIXED, 'w', encoding='utf-8') as f:
        for linha in novas_linhas:
            f.write(f"{linha}\n")

    print(f"\n✅ Correção concluída! Arquivo salvo em: {ARQUIVO_PRED_FIXED}")
    print("Verifique se o número de linhas bate com o gold.txt antes de usar.")

if __name__ == "__main__":
    main()