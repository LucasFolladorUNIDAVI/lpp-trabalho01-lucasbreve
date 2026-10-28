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
ENC_INTERVALO = 20   # segundos entre uma encomenda e a próxima tentativa
ENC_QUANTIDADE = 20  # tecido pedido
ENC_PRAZO = 30       # segundos até expirar
ENC_RECOMPENSA = 40  # algodão ganho ao entregar

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
    "encomenda": None,    # {"id": 1, "quantidade": 20, "prazo": 30} enquanto aberta
    "entregues": 0,
    "expiradas": 0,
}

jogadores = {}  # sid -> {"nome": ..., "papel": ...}
proxima_encomenda = 0     # numera as encomendas (para o prazo saber qual expirar)

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
    sio.start_background_task(producao)      # temporizador de produção
    # servidor -> TODOS: o fato, com a causa (o pedido do Mestre)
    sio.start_background_task(encomendas)    # temporizador das encomendas
    await sio.emit("vila.iniciada", fato(pedido))


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
    sio.start_background_task(obra, nome)    # temporizador da obra
    
async def producao():
    """Temporizador: a cada INTERVALO, produz algodão e avisa todos."""
    while estado["fase"] == "aberta":
        await sio.sleep(INTERVALO)          # sio.sleep, nunca time.sleep
        if estado["fase"] != "aberta":
            break
        estado["algodao"] += estado["producao"]
        await sio.emit("recurso.produzido", fato("temporizador"))


async def obra(nome):
    """Temporizador: depois de TEMPO_OBRA, o tear fica pronto."""
    await sio.sleep(TEMPO_OBRA)
    if estado["fase"] != "aberta":
        return
    estado["trabalhadores"] -= 1            # o tecelão fica livre
    estado["em_obra"] -= 1
    estado["concluidas"] += 1
    estado["producao"] += 5                 # cada tear aumenta a produção de algodão
    estado["tecido"] += 10                  # e entrega tecido (recurso refinado)
    causa = "construcao.iniciada (temporizador)"
    await sio.emit("construcao.concluida", fato(causa, por=nome))
    
@sio.on("vila.encerramento_solicitado")
async def encerrar_vila(sid, dados=None):
    pedido = "vila.encerramento_solicitado"
    # O servidor decide: só o Mestre encerra, e só se a temporada estiver aberta.
    if jogadores[sid]["papel"] != "mestre":
        await recusar(sid, "Só o Mestre pode encerrar a temporada", pedido)
        return
    if estado["fase"] != "aberta":
        await recusar(sid, "A temporada não está aberta", pedido)
        return
    estado["fase"] = "encerrada"
    # servidor -> TODOS. Os temporizadores (producao e obra) conferem a fase
    # e param sozinhos; novas construções passam a ser recusadas.
    await sio.emit("vila.encerrada", fato(pedido))
    
async def encomendas():
    """Temporizador: de tempos em tempos, surge uma encomenda de tecido."""
    global proxima_encomenda
    while estado["fase"] == "aberta":
        await sio.sleep(ENC_INTERVALO)
        if estado["fase"] != "aberta":
            break
        if estado["encomenda"] is not None:
            continue                       # já há uma aberta: não surge outra
        proxima_encomenda += 1
        estado["encomenda"] = {"id": proxima_encomenda,
                               "quantidade": ENC_QUANTIDADE, "prazo": ENC_PRAZO}
        await sio.emit("encomenda.recebida", fato("temporizador"))
        sio.start_background_task(prazo_encomenda, proxima_encomenda)


async def prazo_encomenda(eid):
    """Temporizador: se o prazo acabar sem entrega, a encomenda expira."""
    await sio.sleep(ENC_PRAZO)
    if estado["fase"] != "aberta":
        return
    enc = estado["encomenda"]
    if enc is None or enc["id"] != eid:    # já foi entregue
        return
    estado["encomenda"] = None
    estado["expiradas"] += 1
    causa = "encomenda.recebida (temporizador)"
    await sio.emit("encomenda.expirada", fato(causa))


@sio.on("encomenda.entrega_solicitada")
async def entregar_encomenda(sid, dados=None):
    pedido = "encomenda.entrega_solicitada"
    # Valide TUDO antes de alterar o estado e SEM await no meio:
    # se dois jogadores entregam ao mesmo tempo, só o primeiro vence.
    if estado["fase"] != "aberta":
        motivo = "A temporada não está aberta"
    elif estado["encomenda"] is None:
        motivo = "Não há encomenda aberta (ou ela já expirou)"
    elif estado["tecido"] < estado["encomenda"]["quantidade"]:
        motivo = "Tecido insuficiente"
    else:
        motivo = None

    if motivo:
        await recusar(sid, motivo, pedido)   # só quem pediu recebe
        return

    estado["tecido"] -= estado["encomenda"]["quantidade"]
    estado["algodao"] += ENC_RECOMPENSA
    estado["encomenda"] = None
    estado["entregues"] += 1
    nome = jogadores[sid]["nome"]
    await sio.emit("encomenda.entregue", fato(pedido, por=nome, recompensa=ENC_RECOMPENSA))