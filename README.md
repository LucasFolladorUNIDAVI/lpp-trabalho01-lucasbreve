# Vila em Tempo Real — Tecelagem

Aplicação web em tempo real, no estilo de um jogo de vila cooperativo, feita para o Trabalho 01 de Linguagem de Programação e Paradigmas (Programação Orientada a Eventos), UNIDAVI, Sistemas de Informação, 2026/2.

Vários jogadores constroem **teares** para transformar **algodão** em **tecido** e atender **encomendas com prazo**. O Mestre abre e encerra a temporada. O servidor decide tudo; os clientes só pedem e mostram.

## Integrantes

- Lucas Breve Follador — @LucasFolladorUNIDAVI

## Tecnologias

- Servidor: Python 3, `python-socketio` e `uvicorn`
- Cliente: JavaScript com Vue 3, Phaser 3 e Socket.IO (todos por CDN, sem instalar nada)
- Base: Kit Inicial e Guia de Implementação fornecidos pelo professor

## Como instalar e executar

Pré-requisitos: Python 3 e Git.

```
git clone https://github.com/LucasFolladorUNIDAVI/lpp-trabalho01-lucasbreve.git
cd lpp-trabalho01-lucasbreve
python -m venv .venv
.venv\Scripts\activate          # Windows (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
uvicorn server:app --reload
```

Abra `http://localhost:8000` no navegador (não abra o arquivo direto, com `file://`).

Se o PowerShell bloquear a ativação do ambiente, rode antes
`Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.
Se a porta 8000 estiver ocupada, use `uvicorn server:app --reload --port 8001`.

## Como testar com duas abas

O estado fica na memória do servidor: ao salvar um arquivo, o `--reload` reinicia o servidor e a vila volta ao começo. Recarregue as abas e entre de novo.

1. Abra `http://localhost:8000` em duas abas, lado a lado.
2. Na primeira, digite um nome e entre como **Mestre**. Na segunda, entre como **Jogador**.
3. No Mestre, clique em **Abrir temporada**. Nas duas abas, a fase vira `aberta`, a vila mostra "Temporada aberta" e o algodão passa a subir sozinho (+10 a cada 5 s).
4. No Jogador, clique em **Construir tear**. Algodão cai 50 e os tecelões ocupados sobem. Após 8 s, o tear fica pronto: o tecelão fica livre, a produção aumenta e o tecido sobe 10.
5. **Recusa:** com 3 de 3 tecelões ocupados (ou algodão insuficiente), clique em Construir. Só quem pediu vê a recusa.
6. **Disputa:** abra três abas (Mestre, Jogador A e Jogador B). Com 2 de 3 tecelões ocupados, clique em Construir nas duas abas de jogador quase ao mesmo tempo. Só um consegue; o outro é recusado.
7. **Encomenda:** a cada 20 s surge uma encomenda de 20 de tecido, com prazo de 30 s. Clique em **Entregar encomenda** com tecido suficiente (ganha 40 de algodão). Se o prazo acabar, ela expira para todos.
8. No Mestre, clique em **Encerrar temporada**: a vila escurece, a produção para e qualquer nova ação é recusada.

Em cada aba, o **Painel de eventos** mostra os eventos emitidos (⬆ emit) e escutados (⬇ on), com a causa, os dados e a reação do cliente.

## Perguntas

### 1. Quais eventos o seu sistema emite e escuta?

| Evento | Emite | Escuta | Causa |
|---|---|---|---|
| `estado.sincronizado` | Servidor | Só quem conectou | conexão do cliente |
| `vila.abertura_solicitada` | Mestre | Servidor | clique em "Abrir temporada" |
| `vila.iniciada` | Servidor | Todos | `vila.abertura_solicitada` |
| `construcao.solicitada` | Jogador | Servidor | clique em "Construir tear" |
| `construcao.iniciada` | Servidor | Todos | `construcao.solicitada` |
| `operacao.recusada` | Servidor | Só quem pediu | o pedido recusado |
| `recurso.produzido` | Servidor | Todos | temporizador |
| `construcao.concluida` | Servidor | Todos | `construcao.iniciada` + temporizador |
| `encomenda.recebida` | Servidor | Todos | temporizador |
| `encomenda.entrega_solicitada` | Jogador | Servidor | clique em "Entregar encomenda" |
| `encomenda.entregue` | Servidor | Todos | `encomenda.entrega_solicitada` |
| `encomenda.expirada` | Servidor | Todos | `encomenda.recebida` + temporizador |
| `vila.encerramento_solicitado` | Mestre | Servidor | clique em "Encerrar temporada" |
| `vila.encerrada` | Servidor | Todos | `vila.encerramento_solicitado` |

Padrão de nomes: `objeto.acao_no_passado` para o que o servidor confirma e `objeto.acao_solicitada` para o que o cliente pede.

### 2. Como o sistema sabe quando deve atualizar os outros jogadores?

Os clientes não perguntam nada ao servidor. Quando algo muda, o **servidor emite um evento** (`sio.emit`) para todos os conectados, e cada cliente tem um handler registrado com `socket.on` (no código, `ouvir(...)`) que atualiza o estado e a tela. Há dois gatilhos:

- **Um pedido de jogador:** o cliente emite `construcao.solicitada`, o servidor valida, altera o estado e emite `construcao.iniciada` para todos. Se recusar, emite `operacao.recusada` só para quem pediu.
- **Um temporizador do servidor:** as tarefas em segundo plano (`producao`, `obra`, `encomendas` e `prazo_encomenda`) esperam com `sio.sleep` e emitem `recurso.produzido`, `construcao.concluida`, `encomenda.recebida` e `encomenda.expirada` sem ninguém clicar.

O cliente nunca altera o estado por conta própria: só muda quando chega um evento do servidor.

### 3. Que parte do código mostra claramente o uso do paradigma orientado a eventos?

- **Servidor (`server.py`):** os handlers com `@sio.on("construcao.solicitada")` e similares (a função `construir` escuta o pedido, valida sem `await` no meio e emite o fato) e as tarefas `producao()` e `obra()`, que são temporizadores como fonte de eventos.
- **Cliente (`client/index.html`):** as funções `ouvir(...)` e `pedir(...)`, que envolvem `socket.on` e `socket.emit` e registram cada evento no Painel de eventos, e o bloco de escutas dentro de `entrar()`, em que cada evento do servidor liga a uma reação na tela e na vila.

## Uso de IA

Usei o Claude (Anthropic) como apoio durante o trabalho: para organizar a especificação (`docs/especificacao.md`), conferir o código a cada etapa, achar erros e escrever este README. O código de cada etapa partiu do Guia de Implementação e do Kit Inicial do professor.

O que eu mudei e decidi: Alterei os ícones iniciais para ícones relacionados ao meu tema (tecelagem). Alterei o mapa para que fique ambientado na parte de produção de tecido e produção de algodão da vila (mapa personalizado foi gerado pelo Claude).

## Extras

- Evento próprio: **encomenda com prazo** (`encomenda.recebida`, `encomenda.entrega_solicitada`, `encomenda.entregue`, `encomenda.expirada`), com temporizador de prazo e recusa tratada.
- Recurso refinado: **tecido**, produzido quando um tear é concluído, e usado nas encomendas.
