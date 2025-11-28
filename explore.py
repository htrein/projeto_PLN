#apenas verifica se os dados estão ok   

import json
import argparse
import random
from pathlib import Path

dataset_path = Path('spider_data/dev.json')

def show_examples(data, num=5, randomize=False):
    total = len(data)
    print(f"Dataset carregado! Total de exemplos: {total}")

    if total == 0:
        print("O dataset está vazio.")
        return

    indices = list(range(total))
    if randomize:
        random.shuffle(indices)

    num = min(num, total)
    for i in range(num):
        idx = indices[i]
        exemplo = data[idx]
        print(f"\n--- Exemplo #{i+1} (índice {idx}) ---")
        pergunta = exemplo.get('question') or exemplo.get('utterance') or '<sem pergunta>'
        query = exemplo.get('query') or exemplo.get('sql') or '<sem query>'
        db_id = exemplo.get('db_id') or exemplo.get('database_id') or '<sem db_id>'
        print(f"Pergunta (Input): {pergunta}")
        print(f"SQL Real (Target): {query}")
        print(f"ID do Banco de Dados: {db_id}")


def main():
    parser = argparse.ArgumentParser(description='Explora e mostra exemplos do dataset Spider (dev.json).')
    parser.add_argument('-n', '--num', type=int, default=5, help='Número de exemplos a mostrar (padrão: 5)')
    parser.add_argument('-r', '--random', action='store_true', help='Mostrar exemplos em ordem aleatória')
    parser.add_argument('--path', type=str, default=str(dataset_path), help='Caminho para o arquivo JSON do dataset')
    args = parser.parse_args()

    dataset_file = Path(args.path)
    try:
        with dataset_file.open('r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Erro: Não encontrei o arquivo em {dataset_file}. Verifique o caminho.")
        return
    except json.JSONDecodeError as e:
        print(f"Erro ao ler JSON: {e}")
        return

    if isinstance(data, dict) and 'data' in data and isinstance(data['data'], list):
        data = data['data']

    show_examples(data, num=args.num, randomize=args.random)


if __name__ == '__main__':
    main()