# INF01221 - Projeto PLN

## Estrutura do Repositório

- **`run_inference.py`**: Script principal de inferência. Gera os prompts, consulta o modelo e salva as predições.
- **`prompts.py`**: Módulo de Engenharia de Prompt. Constrói o contexto (Zero-Shot ou Few-Shot) injetando o *schema* do banco de dados.
- **`explore.py`**: Script utilitário para inspeção rápida de exemplos do dataset.
- **`teste_avaliacao.py`**: Script de automação que formata os arquivos de saída (`gold.txt` e `pred.txt`) e executa o avaliador oficial.
- **`evaluation.py`** e **`process_sql.py`**: Scripts oficiais de avaliação do benchmark Spider (não alterar).
- **`spider_data/`**: Pasta (não versionada) contendo os bancos de dados e JSONs.
- **`template-latex/`**: Código fonte do artigo final no formato SBC.

---

## Configuração do Dataset

Devido ao tamanho, o dataset não está incluído no controle de versão.

1. Baixe o dataset **Spider 1.0**: [yale-lily.github.io/spider](https://yale-lily.github.io/spider)
2. A estrutura de pastas deve ficar assim:
   - `spider_data/dev.json`
   - `spider_data/train_spider.json`
   - `spider_data/tables.json`
   - `spider_data/database/` (contendo subpastas com os arquivos `.sqlite`)

---

## Instalação e Pré-requisitos

### 1. Dependências do Sistema (Linux/Ubuntu)

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip

# Necessário apenas se for compilar o artigo LaTeX localmente:
# Tem extensão pra LaTeX no VSCode
sudo apt install -y texlive-latex-extra texlive-fonts-recommended texlive-lang-portuguese
```

### 2. Ambiente Virtual Python

Crie o ambiente isolado e instale as bibliotecas necessárias:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install nltk ollama tqdm

# Baixar recursos do NLTK necessários para o script de avaliação oficial
python3 -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"
```

### 3. Configuração do Modelo (Ollama)

Por enquanto testei inferência com o Ollama Mistral

---

## Como Executar

Certifique-se de que seu ambiente virtual está ativo:

```bash
source .venv/bin/activate
```

### 1. Explorar os Dados (Opcional)

Para visualizar 3 exemplos aleatórios e verificar se o dataset foi lido corretamente:

```bash
python3 explore.py -n 3
```

### 2. Rodar a Inferência

Este passo gera as queries SQL a partir das perguntas em linguagem natural.

Edite as variáveis no topo do arquivo `run_inference.py` para configurar:

- **MODELO**: Nome do modelo baixado no Ollama (ex: `"mistral"`).
- **MAX_EXEMPLOS**: Número de exemplos para teste (use `None` para rodar o dataset todo).
- **NUM_SHOTS**: Número de exemplos no contexto (0 para Zero-Shot, 3 para Few-Shot).

Executar:

```bash
python3 run_inference.py
```

> **Nota sobre Modelos**: O script atual está configurado para usar o cliente Ollama. A lógica de construção de prompts em `prompts.py` é agnóstica ao modelo. Se desejar usar outras APIs (OpenAI, HuggingFace, vLLM), basta alterar apenas a função de chamada dentro de `run_inference.py`; o restante da pipeline permanece igual.

**Saída gerada na raiz:**
- `pred.txt`: As queries geradas pelo modelo.
- `gold.txt`: O gabarito oficial (Ground Truth).

### 3. Avaliar os Resultados

Execute o script de teste para calcular as métricas de Exact Match e Execution Accuracy usando a ferramenta oficial do Spider:

```bash
python3 teste_avaliacao.py
```

Os resultados detalhados (acurácia por nível de dificuldade) serão exibidos no terminal.

---

## Compilação do Artigo

Para gerar o PDF do relatório final (Template SBC):

```bash
cd template-latex
pdflatex -interaction=nonstopmode sbc-template.tex
bibtex sbc-template
pdflatex -interaction=nonstopmode sbc-template.tex
pdflatex -interaction=nonstopmode sbc-template.tex
```