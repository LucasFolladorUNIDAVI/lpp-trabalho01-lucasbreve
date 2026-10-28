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