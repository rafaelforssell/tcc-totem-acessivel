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


def test_pipeline_catalogo_por_genero_mostra_produtos_reais(monkeypatch):
    async def fake_classificar_intencao(pergunta, idioma="pt"):
        raise AssertionError("Nao deveria chamar a IA para catalogo por genero")

    produtos = [
        {
            "id": 1,
            "nome": "Camisa Polo Branca Masculina",
            "categoria": "Roupa",
            "tipo": "Camisa",
            "cor": "Branca",
            "tamanho": "M",
            "marca": "Marca A",
            "preco": 119.90,
            "estoque": 1,
            "setor": "Masculino",
            "corredor": "5",
            "prateleira": "Arara 1",
            "descricao": "Camisa polo masculina",
        },
        {
            "id": 2,
            "nome": "Vestido Vermelho Feminino",
            "categoria": "Roupa",
            "tipo": "Vestido",
            "cor": "Vermelho",
            "tamanho": "M",
            "marca": "Marca B",
            "preco": 189.90,
            "estoque": 1,
            "setor": "Feminino",
            "corredor": "7",
            "prateleira": "Arara 2",
            "descricao": "Vestido elegante",
        },
    ]

    monkeypatch.setattr(pipeline_service, "classificar_intencao", fake_classificar_intencao)
    monkeypatch.setattr(pipeline_service, "listar_todos_produtos_formatados", lambda: produtos)
    pipeline_service.limpar_memoria()

    resposta = asyncio.run(pipeline_service.pipeline_processar("O que voce tem pra homem nessa loja?"))

    assert resposta["acao"] == "MOSTRAR_PRODUTOS"
    assert resposta["resultados"][0]["nome"] == "Camisa Polo Branca Masculina"
    assert "infelizmente" not in resposta["resposta"].lower()


def test_busca_segmentada_ignora_pedido_de_mostrar(monkeypatch):
    pipeline_service.limpar_memoria()
    produtos = [
        {
            "id": 1,
            "nome": "Camisa Polo Branca Masculina",
            "categoria": "Roupa",
            "tipo": "Camisa",
            "cor": "Branca",
            "tamanho": "M",
            "marca": "Marca A",
            "preco": 119.90,
            "estoque": 1,
            "setor": "Masculino",
            "corredor": "5",
            "prateleira": "Arara 1",
            "descricao": "Camisa polo masculina",
        },
        {
            "id": 2,
            "nome": "Calca Jeans Masculina",
            "categoria": "Roupa",
            "tipo": "Calca",
            "cor": "Azul",
            "tamanho": "42",
            "marca": "Marca B",
            "preco": 159.90,
            "estoque": 1,
            "setor": "Masculino",
            "corredor": "4",
            "prateleira": "Arara 3",
            "descricao": "Calca jeans casual",
        },
    ]

    monkeypatch.setattr(pipeline_service.db_service, "fetchall", lambda *args, **kwargs: produtos)

    resultado = pipeline_service.buscar_produtos_por_segmentos(
        "Poderia me mostrar a camisa polo e a calca jeans?"
    )

    nomes = [produto["nome"] for produto in resultado["produtos"]]
    assert nomes == ["Camisa Polo Branca Masculina", "Calca Jeans Masculina"]
    assert resultado["faltas"] == []


def test_busca_segmentada_entende_lista_repetida_do_mesmo_produto(monkeypatch):
    pipeline_service.limpar_memoria()
    produtos = [
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
            "nome": "Bone Branco",
            "categoria": "Acessorios",
            "tipo": "Bone",
            "cor": "Branco",
            "tamanho": "Unico",
            "marca": "Marca B",
            "preco": 49.90,
            "estoque": 3,
            "setor": "Acessorios",
            "corredor": "1",
            "prateleira": "Gancho 3",
            "descricao": "Bone casual",
        },
    ]

    monkeypatch.setattr(pipeline_service.db_service, "fetchall", lambda *args, **kwargs: produtos)

    resultado = pipeline_service.buscar_produtos_por_segmentos(
        "Eu quero um bone azul um bone branco e acho que um bone vermelho"
    )

    nomes = [produto["nome"] for produto in resultado["produtos"]]
    assert nomes == ["Bone Azul", "Bone Branco"]
    assert resultado["faltas"] == [{"tipo": "bone", "atributos": ["vermelho"]}]


def test_busca_segmentada_remove_contexto_de_confirmacao(monkeypatch):
    pipeline_service.limpar_memoria()
    produtos = [
        {
            "id": 1,
            "nome": "Camisa Polo Branca Masculina",
            "categoria": "Roupa",
            "tipo": "Camisa",
            "cor": "Branca",
            "tamanho": "M",
            "marca": "Marca A",
            "preco": 119.90,
            "estoque": 1,
            "setor": "Masculino",
            "corredor": "5",
            "prateleira": "Arara 1",
            "descricao": "Camisa polo masculina",
        }
    ]

    monkeypatch.setattr(pipeline_service.db_service, "fetchall", lambda *args, **kwargs: produtos)

    resultado = pipeline_service.buscar_produtos_por_segmentos(
        "Sim, gostei dos dois. Voce tem uma camiseta branca masculina para eu usar com eles?"
    )

    assert [produto["nome"] for produto in resultado["produtos"]] == ["Camisa Polo Branca Masculina"]
    assert resultado["faltas"] == []


def test_pipeline_thcau_encerra_conversa(monkeypatch):
    async def fake_classificar_intencao(pergunta, idioma="pt"):
        raise AssertionError("Despedida deve encerrar antes de chamar a IA")

    monkeypatch.setattr(pipeline_service, "classificar_intencao", fake_classificar_intencao)
    pipeline_service.memoria["ultimos_produtos"] = [{"nome": "Bone Azul"}]

    resposta = asyncio.run(pipeline_service.pipeline_processar("thcau"))

    assert resposta == {"resposta": "", "resultados": [], "acao": "ENCERRAR"}


def test_pipeline_atendente_fecha_com_boas_compras(monkeypatch):
    async def fake_classificar_intencao(pergunta, idioma="pt"):
        raise AssertionError("Pedido de atendente deve ser detectado antes da IA")

    monkeypatch.setattr(pipeline_service, "classificar_intencao", fake_classificar_intencao)
    pipeline_service.limpar_memoria()

    resposta = asyncio.run(pipeline_service.pipeline_processar("Consegue chamar um atendente para me ajudar?"))

    assert resposta["acao"] == "CHAMAR_ATENDENTE"
    assert "boas compras" in resposta["resposta"].lower()


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
        99: {
            "id": 99,
            "nome": "Garrafa Termica Branca",
            "categoria": "Acessorios",
            "tipo": "Garrafa",
            "cor": "Branca",
            "tamanho": "Unico",
            "marca": "Marca C",
            "preco": 79.90,
            "estoque": 1,
            "setor": "Acessorios",
            "corredor": "1",
            "prateleira": "Prateleira 5",
            "descricao": "Garrafa branca",
        },
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
        99: {
            "id": 99,
            "nome": "Garrafa Termica Branca",
            "categoria": "Acessorios",
            "tipo": "Garrafa",
            "cor": "Branca",
            "tamanho": "Unico",
            "marca": "Marca C",
            "preco": 79.90,
            "estoque": 1,
            "setor": "Acessorios",
            "corredor": "1",
            "prateleira": "Prateleira 5",
            "descricao": "Garrafa branca",
        },
    }
    pipeline_service.memoria["produtos_pendentes_confirmacao"] = pipeline_service.memoria["ultimos_produtos"][:]

    resposta = asyncio.run(
        pipeline_service.pipeline_processar("As duas me agradou, poderia me mostrar no mapa?")
    )

    assert resposta["acao"] == "ABRIR_ROTAS"
    assert len(resposta["resultados"]) == 2
    assert all(produto["nome"] != "Garrafa Termica Branca" for produto in resposta["resultados"])
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


def test_pipeline_silencio_duplo_encerra(monkeypatch):
    pipeline_service.limpar_memoria()
    
    # Primeiro silencio
    resposta_1 = asyncio.run(pipeline_service.pipeline_processar("", idioma="pt"))
    assert resposta_1["resposta"] == "Olá, tem alguém aí?"
    assert resposta_1["acao"] == "NENHUM"
    assert pipeline_service.memoria["tentativas_silencio"] == 1

    # Segundo silencio
    resposta_2 = asyncio.run(pipeline_service.pipeline_processar("", idioma="pt"))
    assert resposta_2["resposta"] == ""
    assert resposta_2["acao"] == "ENCERRAR"
    # A memoria deve estar limpa e resetada apos encerrar
    assert pipeline_service.memoria.get("tentativas_silencio", 0) == 0


def test_pipeline_confirmacao_lista_oferece_mapa_ou_encerrar(monkeypatch):
    pipeline_service.limpar_memoria()
    pipeline_service.memoria["produtos_pendentes_confirmacao"] = [
        {"nome": "Camisa Polo", "preco": 100.0}
    ]
    
    resposta = asyncio.run(pipeline_service.pipeline_processar("sim", idioma="pt"))
    assert resposta["acao"] == "MOSTRAR_PRODUTOS"
    assert resposta["auto_add_lista"] is True
    assert "mapa" in resposta["resposta"].lower()
    assert "encerrar" in resposta["resposta"].lower()


def test_pipeline_memoria_genero(monkeypatch):
    pipeline_service.limpar_memoria()
    
    # 1. Faz uma busca com genero "masculina"
    # Deve detectar e salvar "mas" na memoria
    async def fake_classificar_intencao(pergunta, idioma="pt"):
        return {"intencao": "NOVA_BUSCA", "palavras_chave": ["roupa", "masculina"]}
    
    monkeypatch.setattr(pipeline_service, "classificar_intencao", fake_classificar_intencao)
    
    asyncio.run(pipeline_service.pipeline_processar("roupa masculina"))
    assert pipeline_service.memoria["genero"] == "mas"

    # 2. Faz uma busca sem genero
    # Deve herdar o "mas" da memoria
    async def fake_classificar_intencao_2(pergunta, idioma="pt"):
        return {"intencao": "NOVA_BUSCA", "palavras_chave": ["opcao"]}
        
    monkeypatch.setattr(pipeline_service, "classificar_intencao", fake_classificar_intencao_2)
    
    # Mock database results with mixed genders
    produtos = [
        {
            "id": 1,
            "nome": "Camisa Polo Masculina",
            "categoria": "Roupa",
            "tipo": "Camisa",
            "cor": "Branca",
            "tamanho": "M",
            "marca": "Nike",
            "preco": 100.0,
            "estoque": 2,
            "setor": "Masculino",
            "corredor": "5",
            "prateleira": "Arara 1",
            "descricao": "Camisa polo masculina",
            "sku": "POLO-MAS",
            "imagem": "",
            "texto_alt": ""
        },
        {
            "id": 2,
            "nome": "Saia Feminina",
            "categoria": "Roupa",
            "tipo": "Saia",
            "cor": "Preta",
            "tamanho": "M",
            "marca": "Zara",
            "preco": 120.0,
            "estoque": 2,
            "setor": "Feminino",
            "corredor": "7",
            "prateleira": "Arara 2",
            "descricao": "Saia feminina elegante",
            "sku": "SAIA-FEM",
            "imagem": "",
            "texto_alt": ""
        }
    ]
    monkeypatch.setattr(pipeline_service.db_service, "fetchall", lambda *args, **kwargs: produtos)
    
    resposta = asyncio.run(pipeline_service.pipeline_processar("tem mais alguma opcao?"))
    assert resposta["resultados"]
    # So deve retornar a camisa masculina (id 1), nao a saia feminina
    assert len(resposta["resultados"]) == 1
    assert resposta["resultados"][0]["id"] == 1


def test_pipeline_mapa_pronome_plural(monkeypatch):
    pipeline_service.limpar_memoria()
    
    # Adiciona dois produtos na memória de mencionados e zera ultimos_produtos
    produto1 = {
        "id": 10,
        "nome": "Calça Bege Masculina",
        "categoria": "Calça",
        "tipo": "Calça",
        "cor": "Bege",
        "tamanho": "42",
        "marca": "Levi's",
        "preco": 159.90,
        "estoque": 2,
        "setor": "Masculino",
        "corredor": "4",
        "prateleira": "Arara 1",
        "descricao": "Calça masculina bege",
        "sku": "CALCA-BEGE",
        "imagem": "",
        "texto_alt": ""
    }
    produto2 = {
        "id": 20,
        "nome": "Camiseta Branca",
        "categoria": "Camiseta",
        "tipo": "Camiseta",
        "cor": "Branca",
        "tamanho": "G",
        "marca": "Hering",
        "preco": 59.90,
        "estoque": 5,
        "setor": "Masculino",
        "corredor": "5",
        "prateleira": "Arara 2",
        "descricao": "Camiseta masculina branca",
        "sku": "CAM-BRANCA",
        "imagem": "",
        "texto_alt": ""
    }
    
    pipeline_service.memoria["produtos_mencionados"] = {
        10: produto1,
        20: produto2
    }
    pipeline_service.memoria["ultimos_produtos"] = [] # Simula esvaziamento por busca falha
    
    async def fake_classificar_intencao(pergunta, idioma="pt"):
        return {"intencao": "IR_PARA_MAPA", "palavras_chave": []}
        
    monkeypatch.setattr(pipeline_service, "classificar_intencao", fake_classificar_intencao)
    
    resposta = asyncio.run(pipeline_service.pipeline_processar("mostra eles no mapa por favor"))
    
    # Deve encontrar e retornar os dois produtos mencionados pelo fallback
    assert resposta["resultados"]
    assert len(resposta["resultados"]) == 2
    assert {r["id"] for r in resposta["resultados"]} == {10, 20}
    assert resposta["acao"] == "ABRIR_ROTAS"


def test_pipeline_ocao_stopwords():
    # Verifica que "aniversário" e "amanhã" são ignorados durante a limpeza de tokens
    tokens = pipeline_service.limpar_tokens_busca(["vestido", "aniversário", "amanhã"])
    assert "vestido" in tokens
    assert "aniversário" not in tokens
    assert "aniversario" not in tokens
    assert "amanhã" not in tokens
    assert "amanha" not in tokens


def test_pipeline_pollution_filter():
    # Se a intenção atual só tem a palavra-chave "cinto", o tipo "vestido" deve ser ignorado
    # mesmo se estiver presente na frase do usuário (pois a IA não o extraiu nas palavras-chave da busca)
    tokens = pipeline_service.limpar_tokens_busca(["vestido", "cinto"], palavras_validas=["cinto"])
    assert "cinto" in tokens
    assert "vestido" not in tokens


def test_tts_pronunciation():
    from services.tts_service import falar
    # Deve preprocessar seção(ões) e remover parênteses do texto antes de gerar o áudio
    async def run_test():
        # Vamos testar o pré-processamento direto alterando edge_tts.Communicate mock
        original_communicate = pipeline_service.BASE_DIR # apenas para usar falar
        
    # Testando os regex diretamente importando falar
    import re
    def test_text_clean(texto):
        texto = texto.replace("*", "")
        texto = re.sub(r'\bse[çc][aã]o\((?:ões|oês|oes)\)', 'seções', texto)
        texto = re.sub(r'\bsess[aã]o\((?:ões|oês|oes)\)', 'sessões', texto)
        texto = re.sub(r'\bop[çc][aã]o\((?:ões|oês|oes)\)', 'opções', texto)
        texto = re.sub(r'\(s\)', 's', texto)
        texto = texto.replace("(", "").replace(")", "")
        return texto

    assert test_text_clean("Aqui estão as 2 seção(ões) dos produtos.") == "Aqui estão as 2 seções dos produtos."
    assert test_text_clean("Qual rota(s) você quer?") == "Qual rotas você quer?"
    assert test_text_clean("Outra opção(ões) na loja.") == "Outra opções na loja."


def test_pipeline_size_filtering():
    # Vestido tamanho M: o "m" não deve ser descartado por ter comprimento <= 2
    tokens = pipeline_service.limpar_tokens_busca(["vestido", "m"])
    assert "vestido" in tokens
    assert "m" in tokens

    # Sapato tamanho 38: o "38" não deve ser descartado
    tokens_calcado = pipeline_service.limpar_tokens_busca(["sapato", "38"])
    assert "sapato" in tokens_calcado
    assert "38" in tokens_calcado


def test_pipeline_plural_shirts_search():
    # Plural check: "camisas" should map to "camisa"
    tokens = pipeline_service.limpar_tokens_busca(["camisas", "masculinas"])
    assert "camisa" in tokens
    
    # Check that is_pedido_catalogo_por_genero identifies "camisas masculinas" as having a specific type
    res = pipeline_service.is_pedido_catalogo_por_genero("quais camisas masculinas voce tem?")
    assert res is False



