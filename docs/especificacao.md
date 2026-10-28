# Especificação – Vila Tecelagem

Trabalho 01 · Programação Orientada a Eventos · LPP 2026/2

## 1. Visão geral

Uma tecelagem cooperativa. Vários jogadores acessam a mesma vila e constroem **teares** para transformar **algodão** em **tecido**. O **Mestre** abre e encerra a temporada. Quem decide tudo é o servidor; os jogadores pedem e veem o resultado na hora.

- **Recurso primário:** algodão (produzido automaticamente).
- **Recurso refinado:** tecido (surge quando um tear fica pronto).
- **Trabalhadores:** tecelões (cada obra ocupa um tecelão até terminar).
- **O que expira:** encomenda de tecido com prazo.

## 2. Regras

| Regra | Valor |
|---|---|
| Algodão inicial | 150 |
| Tecido inicial | 0 |
| Limite de tecelões ocupados ao mesmo tempo | 3 |
| Custo de um tear | 50 de algodão |
| Tempo de obra de um tear | 8 segundos |
| Intervalo de produção de algodão | 5 segundos |
| Produção inicial por intervalo | +10 de algodão |
| Ganho ao concluir um tear | +5 de algodão por intervalo (produção permanente) e +10 de tecido |
| Encomenda: surge a cada | 20 segundos (enquanto a temporada está aberta) |
| Encomenda: pede | 20 de tecido |
| Encomenda: prazo | 30 segundos |
| Recompensa ao entregar | +40 de algodão |

Regras de decisão do servidor:

1. Só o Mestre abre e encerra a temporada, e cada uma só acontece uma vez, na ordem: aguardando → aberta → encerrada.
2. Uma construção só é aceita se a temporada está aberta, há algodão suficiente e há tecelão livre. Caso contrário, só quem pediu recebe a recusa.
3. O servidor trata um pedido por vez. Se dois jogadores pedem ao mesmo tempo o último recurso, o primeiro a ser tratado vence e o segundo é recusado.
4. Uma encomenda só pode ser entregue por quem tem tecido suficiente, e apenas enquanto não expirou. A primeira entrega aceita fecha a encomenda; as demais são recusadas.
5. Ao encerrar a temporada, produção, obras e encomendas param, e qualquer novo pedido é recusado.
6. O cliente nunca altera o estado por conta própria: ele só muda quando chega um evento do servidor.

## 3. Tabela de eventos

Padrão de nomes: `objeto.acao_no_passado` para o que o servidor confirma e `objeto.acao_solicitada` para o que o cliente pede.

| Evento | Emite | Recebe | O que muda |
|---|---|---|---|
| estado.sincronizado | Servidor | Só quem conectou | Quem entra recebe o estado atual da tecelagem |
| vila.abertura_solicitada | Mestre | Servidor | Pedido para abrir a temporada |
| vila.iniciada | Servidor | Todos | Temporada passa a "aberta" e a produção de algodão e as encomendas começam |
| construcao.solicitada | Jogador | Servidor | Pedido para construir um tear |
| construcao.iniciada | Servidor | Todos | Pedido aceito: debita 50 de algodão, ocupa 1 tecelão e inicia a obra |
| operacao.recusada | Servidor | Só quem pediu | Faltou algodão, tecelão ou tecido, a encomenda expirou ou a temporada não está aberta; nada muda no estado |
| recurso.produzido | Servidor | Todos | A cada 5 s, o algodão sobe conforme a produção atual |
| construcao.concluida | Servidor | Todos | O tear fica pronto: tecelão livre, +5 de produção de algodão e +10 de tecido |
| encomenda.recebida | Servidor | Todos | Surge uma encomenda de 20 de tecido, com prazo de 30 s |
| encomenda.entrega_solicitada | Jogador | Servidor | Pedido para entregar a encomenda aberta |
| encomenda.entregue | Servidor | Todos | Debita 20 de tecido, credita +40 de algodão e fecha a encomenda |
| encomenda.expirada | Servidor | Todos | O prazo acabou sem entrega: a encomenda é perdida |
| vila.encerramento_solicitado | Mestre | Servidor | Pedido para encerrar a temporada |
| vila.encerrada | Servidor | Todos | Temporada passa a "encerrada" e novas ações são recusadas |

Causa de cada fato (o que o Painel de eventos deve mostrar):

| Fato | Causa |
|---|---|
| estado.sincronizado | conexão do cliente |
| vila.iniciada | vila.abertura_solicitada |
| construcao.iniciada | construcao.solicitada |
| recurso.produzido | temporizador |
| construcao.concluida | construcao.iniciada (temporizador) |
| encomenda.recebida | temporizador |
| encomenda.entregue | encomenda.entrega_solicitada |
| encomenda.expirada | encomenda.recebida (temporizador) |
| vila.encerrada | vila.encerramento_solicitado |

## 4. Cenários de teste

### Cenário 1 – Recusa

- **Dado que** a temporada está aberta, há 150 de algodão e já há 3 de 3 tecelões ocupados,
- **quando** o jogador A emite `construcao.solicitada`,
- **então** o servidor emite `operacao.recusada` (motivo: sem tecelão livre) apenas para A, e o estoque e os tecelões ocupados continuam iguais.

### Cenário 2 – Passagem do tempo

- **Dado que** a temporada está aberta, com 150 de algodão e nenhuma obra em andamento,
- **quando** passam 5 segundos sem que ninguém peça nada,
- **então** o servidor emite `recurso.produzido` para todos (causa: temporizador) e o algodão sobe para 160.
- **E dado que** o jogador A emitiu `construcao.solicitada` e recebeu `construcao.iniciada`,
- **quando** passam 8 segundos,
- **então** o servidor emite `construcao.concluida` para todos (causa: `construcao.iniciada` + temporizador), o tecelão fica livre, a produção sobe para +15 e o tecido sobe para 10.

### Cenário 3 – Disputa entre dois jogadores

- **Dado que** a temporada está aberta e há 2 de 3 tecelões ocupados,
- **quando** os jogadores A e B emitem `construcao.solicitada` ao mesmo tempo,
- **então** o servidor emite `construcao.iniciada` para todos (um tear, pedido de um deles) e `operacao.recusada` apenas para o outro; os tecelões ocupados ficam em 3 de 3 e nunca passam do limite.

### Cenário 4 – Encomenda com prazo (evento próprio)

- **Dado que** a temporada está aberta e uma encomenda de 20 de tecido foi recebida,
- **quando** passam 30 segundos sem nenhuma entrega aceita,
- **então** o servidor emite `encomenda.expirada` para todos (causa: `encomenda.recebida` + temporizador) e uma `encomenda.entrega_solicitada` feita depois disso recebe `operacao.recusada` (motivo: encomenda expirada) apenas para quem pediu.
