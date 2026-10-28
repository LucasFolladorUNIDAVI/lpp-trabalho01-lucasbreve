import socketio

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
app = socketio.ASGIApp(sio, static_files={
    "/": "client/index.html",
    "/assets": "client/assets",      # mapa, tileset e sprites da vila
})

# A partir da Etapa 1, adicione o seu código ABAIXO desta linha.
CUSTO = 50        # algodão por tear
TEMPO_OBRA = 8    # segundos até o tear ficar pronto
INTERVALO = 5     # segundos entre as produções de algodão

estado = {
    "fase": "aguardando",   # aguardando -> aberta -> encerrada
    "algodao": 150,
    "tecido": 0,
    "trabalhadores": 0,     # tecelões ocupados agora
    "limite": 3,            # máximo de tecelões ocupados
    "producao": 10,         # algodão produzido a cada INTERVALO
    "intervalo": INTERVALO,
    "tempo_obra": TEMPO_OBRA,
    "custo": CUSTO,
    "concluidas": 0,
    "em_obra": 0,
}

jogadores = {}  # sid -> {"nome": ..., "papel": ...}


def fato(causa, **extras):
    """Monta o payload de um FATO: estado atual + CAUSA (o evento ou
    temporizador que gerou o fato) + dados extras."""
    return {"estado": dict(estado), "causa": causa, **extras}


@sio.event
async def connect(sid, environ, auth):
    auth = auth or {}
    jogadores[sid] = {
        "nome": auth.get("nome", "Anônimo"),
        "papel": auth.get("papel", "jogador"),
    }
    # servidor -> UM cliente: quem acabou de entrar precisa do estado atual
    await sio.emit("estado.sincronizado", fato("conexao"), to=sid)


@sio.event
async def disconnect(sid):
    jogadores.pop(sid, None)

async def recusar(sid, motivo, causa):
    """Responde só a quem pediu (operacao.recusada)."""
    await sio.emit("operacao.recusada", {"motivo": motivo, "causa": causa}, to=sid)


@sio.on("vila.abertura_solicitada")
async def abrir_vila(sid, dados=None):
    pedido = "vila.abertura_solicitada"
    # O servidor decide: só o Mestre abre, e só uma vez.
    if jogadores[sid]["papel"] != "mestre":
        await recusar(sid, "Só o Mestre pode abrir a temporada", pedido)
        return
    if estado["fase"] != "aguardando":
        await recusar(sid, "A temporada já foi aberta", pedido)
        return
    estado["fase"] = "aberta"
    # servidor -> TODOS: o fato, com a causa (o pedido do Mestre)
    await sio.emit("vila.iniciada", fato(pedido))
    
@sio.on("construcao.solicitada")
async def construir(sid, dados=None):
    pedido = "construcao.solicitada"
    # Ainda SEM validação (de propósito): a Etapa 4 corrige isso.
    estado["algodao"] -= CUSTO
    estado["trabalhadores"] += 1
    estado["em_obra"] += 1
    nome = jogadores[sid]["nome"]
    # servidor -> TODOS: o fato, com a causa (o pedido do jogador) e quem pediu
    await sio.emit("construcao.iniciada", fato(pedido, por=nome))
    
@sio.on("construcao.solicitada")
async def construir(sid, dados=None):
    pedido = "construcao.solicitada"

    # Valide TUDO antes de alterar o estado e SEM await no meio:
    # assim, dois pedidos simultâneos são decididos um de cada vez.
    if estado["fase"] != "aberta":
        motivo = "A temporada não está aberta"
    elif estado["algodao"] < CUSTO:
        motivo = "Algodão insuficiente"
    elif estado["trabalhadores"] >= estado["limite"]:
        motivo = "Sem tecelão livre"
    else:
        motivo = None

    if motivo:
        await recusar(sid, motivo, pedido)   # só quem pediu recebe
        return

    estado["algodao"] -= CUSTO
    estado["trabalhadores"] += 1
    estado["em_obra"] += 1
    nome = jogadores[sid]["nome"]
    await sio.emit("construcao.iniciada", fato(pedido, por=nome))