import json
import os

# 1. Vamos ler o gabarito (dev.json)
with open('spider_data/dev.json', 'r', encoding='utf-8') as f:
    dados = json.load(f)

# 2. Vamos criar os arquivos que o evaluation.py exige
# O 'gold.txt' precisa ter: SQL_Real \t ID_Banco
# O 'pred.txt' precisa ter apenas: SQL_Gerado

print("Gerando arquivos para o script de avaliação...")

with open('gold.txt', 'w') as f_gold, open('pred.txt', 'w') as f_pred:
    # Vamos pegar apenas os 5 primeiros exemplos para testar
    for i in range(5):
        exemplo = dados[i]
        sql_real = exemplo['query']
        db_id = exemplo['db_id']
        
        # Escreve no gabarito
        f_gold.write(f"{sql_real}\t{db_id}\n")
        
        # SIMULAÇÃO: Vamos fingir que nosso modelo é PERFEITO e gerou igual ao real
        # (Se mudarmos isso aqui para algo errado, a nota deve cair)
        f_pred.write(f"{sql_real}\n")

print("Arquivos gold.txt e pred.txt criados!")
print("Agora vamos rodar o script oficial do Spider...")
print("-" * 30)

# 3. Chama o script oficial via comando do sistema
# Ele precisa apontar onde estão os bancos de dados (--db)
os.system("python3 evaluation.py --gold gold.txt --pred pred.txt --db spider_data/database --table spider_data/tables.json --etype match")