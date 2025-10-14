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

## Algoritmo genético
### População inicial
Para gerar a população inicial, foi implementado um algoritmo que gera individuos baseado em 2 tipos de algoritmos, 
escolhidos em tempo de execução, baseado em pesos. Os algoritmos e pesos são:

1. Split into chunks: faz um shuffle da lista de locations e divide as locations em chunks baseado no número de veículos. 
Peso 20% dos individuos da população
2. K-means: agrupa as locations em cluster de locations mais próximas. Peso 80% dos individuos da população