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

### Cruzamento
Para implementar o operador de crossover no algoritmo genético, adotamos uma abordagem baseada na linearização das rotas. Em vez de realizar o cruzamento diretamente sobre a estrutura de múltiplas rotas (uma para cada veículo), primeiro transformamos o indivíduo em uma lista única (“lista flat”) contendo todas as locations em sequência.

Essa transformação permite aplicar qualquer operador de crossover tradicional (nós utilizamos o order-crossover) de forma simples e consistente, pois os dois pais passam a ser apenas sequências lineares de cidades com o mesmo tamanho.

Após realizar o cruzamento entre as duas listas planas (os dois pais), obtemos uma nova sequência de cidades que representa o filho. Em seguida, reconstruímos a estrutura original de rotas, respeitando os tamanhos iniciais de cada rota do indivíduo original.

Exemplo:
Suponha um indivíduo com 3 rotas, sendo:

- Rota 1: 5 cidades 
- Rota 2: 10 cidades 
- Rota 3: 15 cidades

Primeiro, concatenamos as três rotas, formando uma lista única com 30 cidades. Aplicamos então o crossover entre dois pais nesse formato linear. Após gerar o filho, dividimos a lista resultante de volta em 5, 10 e 15 elementos, restaurando as três rotas na mesma proporção original.

Essa técnica permite utilizar operadores de crossover convencionais sem perder a informação estrutural das rotas, garantindo que o filho final preserve a quantidade de rotas e os limites de cada uma.

### Mutação
Para a etapa de mutação, optamos por não trabalhar sobre a lista flat, mas sim diretamente em cada rota individualmente. Isso garante que a estrutura do indivíduo seja preservada e evita que a mutação crie soluções inválidas ou desbalanceadas entre os veículos.

A mutação é aplicada de forma aleatória: selecionamos uma rota do indivíduo e trocamos a posição de dois elementos (cidades) dentro dessa rota. Esse tipo de operação mantém o conteúdo da rota, mas altera a ordem das visitas, permitindo explorar novas possibilidades de solução.

Para controlar a intensidade da diversificação, definimos uma probabilidade de mutação de 10%, ou seja, a cada indivíduo gerado pelo crossover, existe 10% de chance de aplicar a mutação. Isso ajuda a evitar que a população convirja rapidamente para soluções locais, mantendo a diversidade genética ao longo das gerações.

Em resumo:

- A mutação acontece dentro de uma rota, não na lista linearizada. 
- A operação consiste em trocar dois elementos aleatórios da rota. 
- A mutação é aplicada com probabilidade de 10% por indivíduo.
- Essa estratégia mantém a solução válida e, ao mesmo tempo, contribui para a exploração do espaço de busca do problema.