import asyncio
import os
import time

from fastapi.testclient import TestClient

from main import app
from services import pipeline_service, tts_service


client = TestClient(app)


def _fakes(monkeypatch):
    async def fake_classificar_intencao(pergunta, idioma="pt"):
        return {"intencao": "NOVA_BUSCA", "palavras_chave": ["camisa"]}

    async def fake_perguntar_llm(pergunta, contexto_produtos=None, idioma="pt", historico=None, todos_produtos=None):
        return "Encontrei uma camisa para voce."

    monkeypatch.setattr(pipeline_service, "classificar_intencao", fake_classificar_intencao)
    monkeypatch.setattr(pipeline_service, "perguntar_llm", fake_perguntar_llm)


def _historico(sessao_id):
    async def ler():
        pipeline_service.usar_sessao(sessao_id)
        return list(pipeline_service.memoria["historico_conversas"])

    return asyncio.run(ler())


def test_memoria_isolada_por_sessao(monkeypatch):
    _fakes(monkeypatch)
    pipeline_service.limpar_memoria("totem-a")
    pipeline_service.limpar_memoria("totem-b")

    asyncio.run(pipeline_service.pipeline_processar("quero uma camisa", sessao_id="totem-a"))

    assert _historico("totem-a")
    assert _historico("totem-b") == []


def test_reset_limpa_apenas_a_propria_sessao(monkeypatch):
    _fakes(monkeypatch)
    asyncio.run(pipeline_service.pipeline_processar("quero uma camisa", sessao_id="totem-a"))
    asyncio.run(pipeline_service.pipeline_processar("quero uma camisa", sessao_id="totem-b"))

    resposta = client.post("/reset", headers={"X-Session-Id": "totem-b"})

    assert resposta.status_code == 200
    assert _historico("totem-b") == []
    assert _historico("totem-a")


def test_sessao_id_invalido_cai_na_sessao_padrao():
    assert pipeline_service.normalizar_sessao_id("../../etc") == pipeline_service.SESSAO_PADRAO
    assert pipeline_service.normalizar_sessao_id("x" * 100) == pipeline_service.SESSAO_PADRAO
    assert pipeline_service.normalizar_sessao_id("abc-123_DEF") == "abc-123_DEF"


def test_cors_libera_apenas_o_frontend_e_localhost():
    def origem_liberada(origem):
        resposta = client.get("/health", headers={"Origin": origem})
        return resposta.headers.get("access-control-allow-origin") == origem

    assert origem_liberada("https://totem-acessiveltcc.netlify.app")
    assert origem_liberada("http://localhost:5500")
    assert origem_liberada("http://127.0.0.1:8000")
    assert not origem_liberada("https://site-qualquer.example")
    assert not origem_liberada("http://localhost.evil.example")


def test_health_nao_expoe_integracoes():
    payload = client.get("/health").json()

    assert set(payload) == {"status", "db", "produtos", "timestamp"}


def test_health_nao_expoe_detalhe_do_erro(monkeypatch):
    import main

    def falha():
        raise RuntimeError("postgresql://usuario:senha@host/db")

    monkeypatch.setattr(main, "contar_produtos_db", falha)

    resposta = client.get("/health")

    assert resposta.status_code == 503
    assert "senha" not in resposta.text


def test_limpeza_remove_apenas_audios_antigos(tmp_path, monkeypatch):
    monkeypatch.setattr(tts_service, "PASTA_AUDIO", str(tmp_path))
    antigo = tmp_path / "antigo.mp3"
    recente = tmp_path / "recente.mp3"
    outro = tmp_path / "leia.txt"
    for arquivo in (antigo, recente, outro):
        arquivo.write_bytes(b"x")
    velho = time.time() - tts_service.AUDIO_RETENCAO_SEGUNDOS - 60
    os.utime(antigo, (velho, velho))
    os.utime(outro, (velho, velho))

    tts_service.limpar_audios_antigos()

    assert not antigo.exists()
    assert recente.exists()
    assert outro.exists()


def test_audio_de_entrada_apagado_mesmo_com_erro(monkeypatch, tmp_path):
    from routes import query

    monkeypatch.setattr(query, "AUDIO_DIR", str(tmp_path))

    async def stt_com_erro(caminho):
        raise RuntimeError("falha no STT")

    monkeypatch.setattr(query, "transcrever_audio", stt_com_erro)
    cliente_sem_raise = TestClient(app, raise_server_exceptions=False)

    resposta = cliente_sem_raise.post(
        "/query-audio",
        files={"audio": ("audio.webm", b"fake", "audio/webm")},
        data={"idioma": "pt"},
    )

    assert resposta.status_code == 500
    assert list(tmp_path.iterdir()) == []
