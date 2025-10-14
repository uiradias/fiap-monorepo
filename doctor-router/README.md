# Doctor Router

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
python main.py
```

## Geração de rotas
Ao executar o programa, cada solução com melhor fitness do que a anterior, será armazenada em um arquivo JSON para ser 
consumido pelo projeto [doctor-router-chatbot](https://github.com/uiradias/fiap-monorepo/tree/main/doctor-router-chatbot)