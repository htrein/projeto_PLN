import json
import os
import re
import replicate # Nova importação
from tqdm import tqdm

# --- CONFIGURAÇÕES ---
# O modelo no replicate precisa do ID completo. 
# Para Llama 3 8B Instruct (melhor para seguir instruções SQL que o base):
MODELO = "meta/meta-llama-3-8b-instruct" 
ARQUIVO_DADOS = "questions.json"
ARQUIVO_PRED = "pred.txt"
ARQUIVO_GOLD = "gold.txt"

# Limite de execuções para teste
LIMIT = 5


os.environ["REPLICATE_API_TOKEN"] = "" 

def limpar_sql(texto_gerado):
    """
    Tenta extrair apenas o SQL da resposta do modelo.
    """
    padrao_markdown = r"```sql\s*(.*?)\s*```"
    match = re.search(padrao_markdown, texto_gerado, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip().replace('\n', ' ')
    return texto_gerado.replace('\n', ' ').strip()

def chamar_replicate(prompt, modelo):
    """
    Substitui a função chamar_api_remota antiga.
    """
    try:
        # O input varia levemente por modelo, mas para Llama 3 geralmente é assim:
        input_args = {
            "prompt": prompt,
            "max_new_tokens": 4096,
            "temperature": 0.1
        }

        # O replicate.run roda e espera a resposta (sincronamente para você)
        output = replicate.run(
            modelo,
            input=input_args
        )

        # O Replicate geralmente retorna uma lista de strings (tokens), precisamos juntar
        texto_completo = "".join(output)
        return texto_completo

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

                # Chama a nova função do Replicate
                texto_gerado = chamar_replicate(prompt_texto, MODELO)
                
                # Tratamento de erro caso venha um dicionário com erro
                if isinstance(texto_gerado, dict) and 'error' in texto_gerado:
                    tqdm.write(f"Erro API item {i}: {texto_gerado['error']}")
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
