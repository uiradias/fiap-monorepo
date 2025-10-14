# Doctor Router Chatbot

## Executar step-by-step

1. Criar venv
```
python -m venv .venv
```

2. Ativar environment
```
source .venv/bin/activate
```

3. Instalar dependencias
```
pip install -r requirements.txt
```

4. Rodar projeto
```
streamlit run main.py
```

> [!IMPORTANT]
> Gerar um arquivo `.env` com a variavel de ambiente `OPENAI_API_KEY` e sua chave de acesso ao OpenAI

## Integração com LLM (OpenAI)
A integração com LLM cria uma cadeia (chain) de Pergunta e Resposta baseada em recuperação (RetrievalQA) usando LangChain.
A pipeline de Perguntas e Respostas é gerado com os seguintes passos:

1. O usuário faz uma pergunta.
2. O sistema busca os 3 documentos mais relevantes no `vector_store`.
3. Os documentos são inseridos no prompt junto da pergunta.
4. O ChatOpenAI gera uma resposta usando o contexto recuperado.
