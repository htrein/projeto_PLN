import json
import os
import ollama
import re
from tqdm import tqdm
from prompts import criar_prompt_basico

# --- CONFIGURAÇÕES ---
MODELO = "mistral"       # O modelo que você baixou (mistral, llama3, qwen2.5:0.5b)
PASTA_DADOS = "spider_data"  # Nome da pasta onde estão os JSONs e a pasta database
MAX_EXEMPLOS = 10        # Comece com 10 para testar rápido. Mude para None para rodar TUDO.

def limpar_sql(texto_gerado):
    """
    Tenta extrair apenas o SQL da resposta do modelo.
    Modelos gostam de falar: "Here is the SQL: SELECT...", nós queremos só o SELECT.
    """
    # 1. Remove blocos de código markdown (```sql ... ```)
    padrao_markdown = r"```sql\s*(.*?)\s*```"
    match = re.search(padrao_markdown, texto_gerado, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    # 2. Se não tiver markdown, tenta limpar quebras de linha extras e pega o texto cru
    # (Pode ser melhorado com regex para pegar frases começando com SELECT)
    return texto_gerado.replace('\n', ' ').strip()

def main():
    print(f"Iniciando inferência com modelo: {MODELO}")
    
    # Caminhos dos arquivos
    caminho_dev = os.path.join(PASTA_DADOS, 'dev.json')
    caminho_db = os.path.join(PASTA_DADOS, 'database')
    
    # Verifica se a pasta database existe (ajuste de caminho comum)
    if not os.path.exists(caminho_db):
        # Tenta procurar dentro de spider_data/spider_data se o zip extraiu duplicado
        caminho_db_alternativo = os.path.join(PASTA_DADOS, 'spider_data', 'database')
        if os.path.exists(caminho_db_alternativo):
            caminho_db = caminho_db_alternativo
            print(f"Aviso: Usando caminho alternativo para bancos: {caminho_db}")

    # Carrega dataset
    try:
        with open(caminho_dev, 'r') as f:
            dataset = json.load(f)
    except FileNotFoundError:
        print(f"❌ Erro: Não encontrei {caminho_dev}. Verifique o nome da pasta.")
        return

    # Limita quantidade para teste
    amostra = dataset[:MAX_EXEMPLOS] if MAX_EXEMPLOS else dataset
    
    print(f"Processando {len(amostra)} exemplos...")

    # Abre arquivos de saída
    with open('pred.txt', 'w') as f_pred, open('gold.txt', 'w') as f_gold:
        
        # Loop com barra de progresso
        for item in tqdm(amostra):
            try:
                # 1. Gera o Prompt (usando seu script anterior)
                prompt = criar_prompt_basico(item['question'], item['db_id'], pasta_bancos=caminho_db)
                
                # 2. Chama a IA
                response = ollama.generate(model=MODELO, prompt=prompt)
                texto_gerado = response['response']
                
                # 3. Limpa a resposta
                sql_final = limpar_sql(texto_gerado)
                
                # Tratamento de erro vazio
                if not sql_final: 
                    sql_final = "SELECT * FROM erro_geracao"

                # 4. Salva (Gabarito e Predição)
                f_pred.write(f"{sql_final}\n")
                f_gold.write(f"{item['query']}\t{item['db_id']}\n")
                
            except Exception as e:
                print(f"\nErro no item {item['question']}: {e}")
                # Salva placeholder para não desalistar os arquivos
                f_pred.write("SELECT error FROM model\n")
                f_gold.write(f"{item['query']}\t{item['db_id']}\n")

    print("\n✅ Concluído!")
    print("Arquivos gerados: 'pred.txt' (IA) e 'gold.txt' (Gabarito)")
    print("Agora rode: python3 evaluation.py --gold gold.txt --pred pred.txt --db spider_data/database --table spider_data/tables.json --etype match")

if __name__ == "__main__":
    main()