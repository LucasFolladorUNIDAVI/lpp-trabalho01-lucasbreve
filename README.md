# Vila em Tempo Real — (tecelagem)
Aplicação web em tempo real, no estilo de um jogo de vila cooperativo, feita para o Trabalho 01 de Linguagem de Programação e Paradigmas (Programação Orientada a Eventos), UNIDAVI, Sistemas de Informação, 2026/2.
Vários jogadores constroem teares para transformar algodão em tecido e atender encomendas com prazo. O Mestre abre e encerra a temporada. O servidor decide tudo; os clientes só pedem e mostram.

## Integrante
- Lucas Breve Follador — @LucasFolladorUNIDAVI

## Tecnologias
Servidor: Python 3, python-socketio e uvicorn
Cliente: JavaScript com Vue 3, Phaser 3 e Socket.IO (todos por CDN, sem instalar nada)
Base: Kit Inicial e Guia de Implementação fornecidos pelo professor

## Como instalar e executar
Pré-requisitos: Python 3 e Git.

git clone https://github.com/LucasFolladorUNIDAVI/lpp-trabalho01-lucasbreve.git
cd lpp-trabalho01-lucasbreve
python -m venv .venv
.venv\Scripts\activate          # Windows (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
uvicorn server:app --reload

Abra http://localhost:8000 no navegador (não abra o arquivo direto, com file://).
Se o PowerShell bloquear a ativação do ambiente, rode antes Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass. Se a porta 8000 estiver ocupada, use uvicorn server:app --reload --port 8001.

## Como testar com duas abas
O estado fica na memória do servidor: ao salvar um arquivo, o --reload reinicia o servidor e a vila volta ao começo. Recarregue as abas e entre de novo.

1. Abra http://localhost:8000 em duas abas, lado a lado.
2. Na primeira, digite um nome e entre como Mestre. Na segunda, entre como Jogador.
3. No Mestre, clique em Abrir temporada. Nas duas abas, a fase vira aberta, a vila mostra "Temporada aberta" e o algodão passa a subir sozinho (+10 a cada 5 s).
4. No Jogador, clique em Construir tear. Algodão cai 50 e os tecelões ocupados sobem. Após 8 s, o tear fica pronto: o tecelão fica livre, a produção aumenta e o tecido sobe 10.
5. Recusa: com 3 de 3 tecelões ocupados (ou algodão insuficiente), clique em Construir. Só quem pediu vê a recusa.
6. Disputa: abra três abas (Mestre, Jogador A e Jogador B). Com 2 de 3 tecelões ocupados, clique em Construir nas duas abas de jogador quase ao mesmo tempo. Só um consegue; o outro é recusado.
7. Encomenda: a cada 20 s surge uma encomenda de 20 de tecido, com prazo de 30 s. Clique em Entregar encomenda com tecido suficiente (ganha 40 de algodão). Se o prazo acabar, ela expira para todos.
8. No Mestre, clique em Encerrar temporada: a vila escurece, a produção para e qualquer nova ação é recusada.

Em cada aba, o Painel de eventos mostra os eventos emitidos (⬆ emit) e escutados (⬇ on), com a causa, os dados e a reação do cliente.

## Perguntas
1. Quais eventos o seu sistema emite e escuta?
3. Como o sistema sabe quando deve atualizar os outros jogadores?
4. Que parte do código mostra claramente o uso do paradigma orientado a eventos?

## Uso de IA


## Extras

