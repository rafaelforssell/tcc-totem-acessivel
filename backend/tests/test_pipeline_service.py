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

    pipeline_service.memoria["historico_conversas"] = [{"role": "assistant", "content": "Gostou dessa opcao?"}]
    pipeline_service.memoria["produtos_pendentes_confirmacao"] = pipeline_service.memoria["ultimos_produtos"][:]

    resposta = asyncio.run(pipeline_service.pipeline_processar("Gostei das duas"))

    assert resposta["acao"] == "MOSTRAR_PRODUTOS"
    assert resposta["auto_add_lista"] is True
    assert resposta["resultados"][0]["nome"] == "Camiseta Basica"


def test_pipeline_nao_abre_mapa_por_confirmacao_generica(monkeypatch):
    async def fake_classificar_intencao(pergunta, idioma="pt"):
        return {"intencao": "OUTROS", "palavras_chave": []}

    monkeypatch.setattr(pipeline_service, "classificar_intencao", fake_classificar_intencao)
    pipeline_service.memoria["ultimos_produtos"] = [
        {
            "id": 1,
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
    pipeline_service.memoria["historico_conversas"] = [{"role": "assistant", "content": "Gostou?"}]
    pipeline_service.memoria["produtos_pendentes_confirmacao"] = []

    resposta = asyncio.run(pipeline_service.pipeline_processar("sim"))

    assert resposta["acao"] == "NENHUM"


def test_pipeline_avisa_falta_cor_e_sugere_opcao_parecida(monkeypatch):
    async def fake_classificar_intencao(pergunta, idioma="pt"):
        return {"intencao": "NOVA_BUSCA", "palavras_chave": ["bone", "vestido", "preto"]}

    monkeypatch.setattr(pipeline_service, "classificar_intencao", fake_classificar_intencao)
    pipeline_service.limpar_memoria()

    resposta = asyncio.run(pipeline_service.pipeline_processar("Eu quero um bone e um vestido preto"))

    nomes = [produto["nome"].lower() for produto in resposta["resultados"]]
    assert resposta["acao"] == "MOSTRAR_PRODUTOS"
    assert any("vestido" in nome for nome in nomes)
    assert not any("casaco" in nome for nome in nomes)
    assert "nao encontrei vestido preto" in resposta["resposta"].lower()


def test_pipeline_nao_trata_negacao_como_atributo_do_produto(monkeypatch):
    async def fake_classificar_intencao(pergunta, idioma="pt"):
        return {"intencao": "NOVA_BUSCA", "palavras_chave": ["bermuda"]}

    monkeypatch.setattr(pipeline_service, "classificar_intencao", fake_classificar_intencao)
    pipeline_service.limpar_memoria()

    resposta = asyncio.run(pipeline_service.pipeline_processar("Nao, voce tem bermuda?"))

    assert resposta["acao"] == "MOSTRAR_PRODUTOS"
    assert resposta["resultados"]
    assert "nao encontrei bermuda nao" not in resposta["resposta"].lower()


def test_pipeline_pedido_explicito_de_mapa_nao_pede_confirmacao_de_novo(monkeypatch):
    async def fake_classificar_intencao(pergunta, idioma="pt"):
        return {"intencao": "IR_PARA_MAPA", "palavras_chave": []}

    monkeypatch.setattr(pipeline_service, "classificar_intencao", fake_classificar_intencao)
    pipeline_service.memoria["ultimos_produtos"] = [
        {
            "id": 1,
            "nome": "Vestido Vermelho Feminino",
            "categoria": "Roupa",
            "tipo": "Vestido",
            "cor": "Vermelho",
            "tamanho": "M",
            "marca": "Marca X",
            "preco": 189.90,
            "estoque": 1,
            "setor": "Feminino",
            "corredor": "7",
            "prateleira": "Arara 2",
            "descricao": "Vestido elegante",
        },
        {
            "id": 2,
            "nome": "Tenis Branco Masculino",
            "categoria": "Calcados",
            "tipo": "Tenis",
            "cor": "Branco",
            "tamanho": "42",
            "marca": "Marca Y",
            "preco": 249.90,
            "estoque": 1,
            "setor": "Masculino",
            "corredor": "3",
            "prateleira": "Prateleira 1",
            "descricao": "Tenis casual",
        },
    ]
    pipeline_service.memoria["produtos_mencionados"] = {
        1: pipeline_service.memoria["ultimos_produtos"][0],
        2: pipeline_service.memoria["ultimos_produtos"][1],
    }
    pipeline_service.memoria["produtos_pendentes_confirmacao"] = pipeline_service.memoria["ultimos_produtos"][:]

    resposta = asyncio.run(pipeline_service.pipeline_processar("Me mostra o mapa dos dois por favor"))

    assert resposta["acao"] == "ABRIR_ROTAS"
    assert "gostaria de ver" not in resposta["resposta"].lower()


def test_pipeline_mapa_dos_dois_mostra_duas_rotas(monkeypatch):
    async def fake_classificar_intencao(pergunta, idioma="pt"):
        return {"intencao": "IR_PARA_MAPA", "palavras_chave": []}

    monkeypatch.setattr(pipeline_service, "classificar_intencao", fake_classificar_intencao)
    pipeline_service.memoria["ultimos_produtos"] = [
        {
            "id": 1,
            "nome": "Bone Azul",
            "categoria": "Acessorios",
            "tipo": "Bone",
            "cor": "Azul",
            "tamanho": "Unico",
            "marca": "Marca A",
            "preco": 49.90,
            "estoque": 3,
            "setor": "Acessorios",
            "corredor": "1",
            "prateleira": "Gancho 2",
            "descricao": "Bone casual",
        },
        {
            "id": 2,
            "nome": "Camisa Branca Feminina",
            "categoria": "Roupa",
            "tipo": "Camisa",
            "cor": "Branca",
            "tamanho": "M",
            "marca": "Marca B",
            "preco": 119.90,
            "estoque": 1,
            "setor": "Feminino",
            "corredor": "5",
            "prateleira": "Arara 4",
            "descricao": "Camisa leve",
        },
    ]
    pipeline_service.memoria["produtos_mencionados"] = {
        1: pipeline_service.memoria["ultimos_produtos"][0],
        2: pipeline_service.memoria["ultimos_produtos"][1],
    }
    pipeline_service.memoria["produtos_pendentes_confirmacao"] = pipeline_service.memoria["ultimos_produtos"][:]

    resposta = asyncio.run(
        pipeline_service.pipeline_processar("As duas me agradou, poderia me mostrar no mapa?")
    )

    assert resposta["acao"] == "ABRIR_ROTAS"
    assert len(resposta["resultados"]) == 2
    corredores = {produto["corredor"] for produto in resposta["resultados"]}
    assert corredores == {"1", "5"}


def test_pipeline_sim_apos_mapa_nao_adiciona_lista(monkeypatch):
    async def fake_classificar_intencao(pergunta, idioma="pt"):
        return {"intencao": "OUTROS", "palavras_chave": []}

    monkeypatch.setattr(pipeline_service, "classificar_intencao", fake_classificar_intencao)
    pipeline_service.memoria["ultimos_produtos"] = [
        {
            "id": 2,
            "nome": "Tenis Branco Masculino",
            "categoria": "Calcados",
            "tipo": "Tenis",
            "cor": "Branco",
            "tamanho": "42",
            "marca": "Marca Y",
            "preco": 249.90,
            "estoque": 1,
            "setor": "Masculino",
            "corredor": "3",
            "prateleira": "Prateleira 1",
            "descricao": "Tenis casual",
        }
    ]
    pipeline_service.memoria["produtos_pendentes_confirmacao"] = []

    resposta = asyncio.run(pipeline_service.pipeline_processar("sim"))

    assert resposta["acao"] == "NENHUM"
    assert resposta.get("auto_add_lista") is None or resposta.get("auto_add_lista") is False


def test_pipeline_encerrar_nao_responde_com_fala(monkeypatch):
    async def fake_classificar_intencao(pergunta, idioma="pt"):
        return {"intencao": "OUTROS", "palavras_chave": []}

    monkeypatch.setattr(pipeline_service, "classificar_intencao", fake_classificar_intencao)
    pipeline_service.memoria["ultimos_produtos"] = [{"nome": "Camiseta Basica"}]

    resposta = asyncio.run(pipeline_service.pipeline_processar("encerrar"))

    assert resposta == {"resposta": "", "resultados": [], "acao": "ENCERRAR"}
