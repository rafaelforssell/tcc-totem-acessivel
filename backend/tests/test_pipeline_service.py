import asyncio

from services import pipeline_service


def test_pipeline_nova_busca_com_ia_mockada(monkeypatch):
    async def fake_classificar_intencao(pergunta, idioma="pt"):
        return {"intencao": "NOVA_BUSCA", "palavras_chave": ["camisa"]}

    async def fake_perguntar_llm(pergunta, contexto_produtos=None, idioma="pt"):
        assert "Camisa" in contexto_produtos
        return "Encontrei uma camisa para voce."

    monkeypatch.setattr(pipeline_service, "classificar_intencao", fake_classificar_intencao)
    monkeypatch.setattr(pipeline_service, "perguntar_llm", fake_perguntar_llm)
    pipeline_service.memoria["ultimos_produtos"] = []

    resposta = asyncio.run(pipeline_service.pipeline_processar("quero uma camisa"))

    assert resposta["acao"] == "MOSTRAR_PRODUTOS"
    assert resposta["resultados"]
    assert "camisa" in resposta["resultados"][0]["nome"].lower()


def test_pipeline_ir_para_mapa_usa_memoria(monkeypatch):
    async def fake_classificar_intencao(pergunta, idioma="pt"):
        return {"intencao": "IR_PARA_MAPA", "palavras_chave": []}

    monkeypatch.setattr(pipeline_service, "classificar_intencao", fake_classificar_intencao)
    pipeline_service.memoria["ultimos_produtos"] = [
        {
            "nome": "Camisa Dry Fit",
            "categoria": "Roupa",
            "tipo": "Treino",
            "cor": "Preta",
            "tamanho": "GG",
            "marca": "Nike",
            "preco": 79.90,
            "estoque": 8,
            "setor": "Esportivo",
            "corredor": "7",
            "prateleira": "Arara 9",
            "descricao": "Camisa esportiva respiravel",
        }
    ]

    resposta = asyncio.run(pipeline_service.pipeline_processar("onde fica?"))

    assert resposta["acao"] == "ABRIR_MAPA"
    assert resposta["resultados"][0]["corredor"] == "7"


def test_pipeline_sim_abre_mapa_quando_tem_produto_em_memoria(monkeypatch):
    async def fake_classificar_intencao(pergunta, idioma="pt"):
        return {"intencao": "OUTROS", "palavras_chave": []}

    monkeypatch.setattr(pipeline_service, "classificar_intencao", fake_classificar_intencao)
    pipeline_service.memoria["ultimos_produtos"] = [
        {
            "nome": "Camiseta Basica",
            "categoria": "Roupa",
            "tipo": "Camiseta",
            "cor": "Preta",
            "tamanho": "M",
            "marca": "Hering",
            "preco": 49.90,
            "estoque": 15,
            "setor": "Masculino",
            "corredor": "1",
            "prateleira": "Arara 1",
            "descricao": "Camiseta 100% algodao",
        }
    ]

    resposta = asyncio.run(pipeline_service.pipeline_processar("Sim, por favor"))

    assert resposta["acao"] == "ABRIR_MAPA"
    assert resposta["resultados"][0]["nome"] == "Camiseta Basica"


def test_pipeline_encerrar_nao_responde_com_fala(monkeypatch):
    async def fake_classificar_intencao(pergunta, idioma="pt"):
        return {"intencao": "OUTROS", "palavras_chave": []}

    monkeypatch.setattr(pipeline_service, "classificar_intencao", fake_classificar_intencao)
    pipeline_service.memoria["ultimos_produtos"] = [{"nome": "Camiseta Basica"}]

    resposta = asyncio.run(pipeline_service.pipeline_processar("encerrar"))

    assert resposta == {"resposta": "", "resultados": [], "acao": "ENCERRAR"}
