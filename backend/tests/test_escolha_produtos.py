import asyncio
from datetime import datetime, timedelta

from services import pipeline_service, telegram_service


def _conversar(monkeypatch, falas, gostei_vira_busca=False):
    """Roda uma conversa no pipeline com a IA (Groq) substituída por regras fixas."""
    async def fake_classificar_intencao(pergunta, idioma="pt"):
        texto = pipeline_service.normalizar_texto(pergunta)
        if any(t in texto for t in ["mapa", "onde", "caminho"]):
            return {"intencao": "IR_PARA_MAPA", "palavras_chave": []}
        if "gostei" in texto and gostei_vira_busca:
            # A IA real pode entender "gostei da masculina" como uma busca nova.
            return {"intencao": "NOVA_BUSCA", "palavras_chave": ["masculina"]}
        if "gostei" in texto:
            return {"intencao": "SOBRE_PRODUTO", "palavras_chave": []}
        palavras = ["camisa" if p == "camiseta" else p for p in pipeline_service.extrair_palavras_busca(texto)]
        return {"intencao": "NOVA_BUSCA", "palavras_chave": palavras}

    async def fake_perguntar_llm(pergunta, contexto_produtos=None, **kwargs):
        return "Resposta da IA."

    monkeypatch.setattr(pipeline_service, "classificar_intencao", fake_classificar_intencao)
    monkeypatch.setattr(pipeline_service, "perguntar_llm", fake_perguntar_llm)
    pipeline_service.limpar_memoria()

    resposta = None
    for fala in falas:
        resposta = asyncio.run(pipeline_service.pipeline_processar(fala))
    return resposta


def _nomes(resposta):
    return [produto["nome"] for produto in resposta["resultados"]]


def test_atendente_recebe_so_o_produto_escolhido_pelo_genero(monkeypatch):
    resposta = _conversar(monkeypatch, [
        "quero uma camiseta preta",
        "gostei da masculina",
        "quero ver no mapa",
        "chama um atendente",
    ])

    assert resposta["acao"] == "CHAMAR_ATENDENTE"
    assert _nomes(resposta) == ["Camisa Polo Preta Masculina"]


def test_escolha_vale_mesmo_se_a_ia_entender_como_nova_busca(monkeypatch):
    resposta = _conversar(monkeypatch, [
        "quero uma camiseta preta",
        "gostei da masculina",
        "chama um atendente",
    ], gostei_vira_busca=True)

    assert _nomes(resposta) == ["Camisa Polo Preta Masculina"]


def test_escolha_e_pedido_de_mapa_na_mesma_frase(monkeypatch):
    resposta = _conversar(monkeypatch, [
        "quero uma camiseta preta",
        "gostei da masculina, onde fica?",
    ])

    assert resposta["acao"] == "ABRIR_MAPA"
    assert _nomes(resposta) == ["Camisa Polo Preta Masculina"]


def test_escolha_por_posicao(monkeypatch):
    resposta = _conversar(monkeypatch, ["quero uma camiseta preta", "gostei da segunda"])

    assert _nomes(resposta) == ["Camisa Preta Feminina"]
    assert resposta["auto_add_lista"] is True


def test_frase_ambigua_nao_escolhe_nada(monkeypatch):
    _conversar(monkeypatch, ["quero uma camiseta preta", "gostei da preta"])

    assert pipeline_service.memoria["produtos_escolhidos"] == []


def test_escolhas_acumulam_ao_longo_da_sessao(monkeypatch):
    resposta = _conversar(monkeypatch, [
        "quero uma camiseta preta",
        "gostei da masculina",
        "quero uma calca jeans",
        "gostei da primeira",
        "chama um atendente",
    ])

    assert _nomes(resposta) == ["Camisa Polo Preta Masculina", "Calça Jeans Masculina"]


def test_ir_ao_caixa_usa_so_o_que_foi_escolhido(monkeypatch):
    resposta = _conversar(monkeypatch, [
        "quero uma camiseta preta",
        "vou levar a masculina",
    ])

    assert resposta["acao"] == "ABRIR_ROTAS"
    assert _nomes(resposta) == ["Camisa Polo Preta Masculina", "Caixas"]


def test_horario_do_telegram_usa_fuso_de_sao_paulo(monkeypatch):
    enviado = {}

    class RespostaFalsa:
        def raise_for_status(self):
            pass

    class ClienteFalso:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def post(self, url, data=None, **kwargs):
            enviado.update(data)
            return RespostaFalsa()

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token-de-teste")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "1")
    monkeypatch.setattr(telegram_service.httpx, "AsyncClient", ClienteFalso)

    resultado = asyncio.run(telegram_service.enviar_alerta_atendente(None, "Totem 1", []))

    assert resultado["ok"] is True
    assert telegram_service.FUSO_LOJA.utcoffset(datetime.now()) == timedelta(hours=-3)
    assert "Horario:" in enviado["text"]
