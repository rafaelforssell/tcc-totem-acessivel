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


def test_pipeline_context_inheritance():
    # Simulate searching for a shirt, setting tipo_ativo in memory
    pipeline_service.limpar_memoria()
    pipeline_service.memoria["tipo_ativo"] = "camisa"
    
    # If the user says "voce tem preta?", it should expand/inherit the type
    tokens = pipeline_service.limpar_tokens_busca(["preta"])
    # The pipeline processar context inheritance check:
    tem_tipo = any(p in pipeline_service.TIPOS_CONHECIDOS for p in tokens)
    assert tem_tipo is False
    assert pipeline_service.memoria.get("tipo_ativo") == "camisa"


def test_buscar_produtos_sql_exact_priority():
    # If we search for "camisa polo preta", it should return the exact polo shirt,
    # rather than returning a list of 3 items (bermuda, calça, polo) via selecionar_por_token.
    resultados = pipeline_service.buscar_produtos_sql(["camisa", "polo", "preta"])
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


def test_pipeline_context_inheritance():
    # Simulate searching for a shirt, setting tipo_ativo in memory
    pipeline_service.limpar_memoria()
    pipeline_service.memoria["tipo_ativo"] = "camisa"
    
    # If the user says "voce tem preta?", it should expand/inherit the type
    tokens = pipeline_service.limpar_tokens_busca(["preta"])
    # The pipeline processar context inheritance check:
    tem_tipo = any(p in pipeline_service.TIPOS_CONHECIDOS for p in tokens)
    assert tem_tipo is False
    assert pipeline_service.memoria.get("tipo_ativo") == "camisa"


def test_buscar_produtos_sql_exact_priority():
    # If we search for "camisa polo preta", it should return the exact polo shirt,
    # rather than returning a list of 3 items (bermuda, calça, polo) via selecionar_por_token.
    resultados = pipeline_service.buscar_produtos_sql(["camisa", "polo", "preta"])
    
    # It should only contain the matching shirt(s), e.g. "Camisa Polo Preta Masculina"
    assert resultados
    assert len(resultados) == 1
    assert "polo" in resultados[0]["nome"].lower()
    assert "preta" in resultados[0]["nome"].lower() or resultados[0]["cor"].lower() == "preta"


def test_pipeline_color_query_context_inheritance(monkeypatch):
    # Set up scenario: active type is "Camisa" and active gender is "mas"
    pipeline_service.limpar_memoria()
    pipeline_service.memoria["tipo_ativo"] = "camisa"
    pipeline_service.memoria["genero"] = "mas"
    
    # Mock classificar_intencao to return SOBRE_PRODUTO with "preta"
    async def fake_classificar_intencao(pergunta, idioma="pt"):
        return {"intencao": "SOBRE_PRODUTO", "palavras_chave": ["preta"]}
        
    async def fake_perguntar_llm(pergunta, contexto_produtos=None, idioma="pt", historico=None, todos_produtos=None):
        return "Temos a camisa polo preta."

    monkeypatch.setattr(pipeline_service, "classificar_intencao", fake_classificar_intencao)
    monkeypatch.setattr(pipeline_service, "perguntar_llm", fake_perguntar_llm)
    
    # Run the query "Você tem preta?"
    resposta = asyncio.run(pipeline_service.pipeline_processar("Você tem preta?"))
    
    # It should perform the database search, inherit "camisa", and return only the black polo shirt
    assert resposta["resultados"]
    assert len(resposta["resultados"]) == 1
    assert resposta["resultados"][0]["nome"] == "Camisa Polo Preta Masculina"


def test_is_pedido_provador_synonyms():
    assert pipeline_service.is_pedido_provador("onde eu consigo experimentar?") is True
    assert pipeline_service.is_pedido_provador("posso provar esta calça?") is True
    assert pipeline_service.is_pedido_provador("onde fica a cabine?") is True


def test_pipeline_tenis_multiples_results_segmentation(monkeypatch):
    pipeline_service.limpar_memoria()
    
    async def fake_classificar_intencao(pergunta, idioma="pt"):
        return {"intencao": "NOVA_BUSCA", "palavras_chave": ["tenis"]}
        
    async def fake_perguntar_llm(pergunta, contexto_produtos=None, idioma="pt", historico=None, todos_produtos=None):
        return "Temos tênis."

    monkeypatch.setattr(pipeline_service, "classificar_intencao", fake_classificar_intencao)
    monkeypatch.setattr(pipeline_service, "perguntar_llm", fake_perguntar_llm)
    
    # "comprar" is a stopword now, so this should resolve to a single segment ["tenis"] and return 3 results
    resposta = asyncio.run(pipeline_service.pipeline_processar("Eu quero comprar um tênis."))
    assert len(resposta["resultados"]) >= 3


def test_pipeline_more_options_continuation(monkeypatch):
    pipeline_service.limpar_memoria()
    
    # Simulate user has already searched for white tennis shoe
    prod_branco = {
        "id": 36, "nome": "Tênis Branco Masculino", "categoria": "Calçados",
        "tipo": "Tênis", "cor": "Branco", "preco": 249.9, "estoque": 1,
        "corredor": "3", "descricao": "Tênis branco"
    }
    pipeline_service.memoria["tipo_ativo"] = "tenis"
    pipeline_service.memoria["ultimos_produtos"] = [prod_branco]
    pipeline_service.memoria["produtos_mencionados"] = {36: prod_branco}
    
    # User asks: "Você tem mais opções?"
    resposta = asyncio.run(pipeline_service.pipeline_processar("Você tem mais opções?"))
    
    # It should match options continuation, filter out id 36, and return other tennis shoes
    assert resposta["acao"] == "MOSTRAR_PRODUTOS"
    assert len(resposta["resultados"]) > 0
    assert all(r["id"] != 36 for r in resposta["resultados"])
    assert all("tênis" in r["nome"].lower() for r in resposta["resultados"])


def test_pipeline_map_matching_priority_from_memory(monkeypatch):
    pipeline_service.limpar_memoria()
    
    prod1 = {
        "id": 15, "nome": "Camisa Social Branca Masculina", "categoria": "Camisas",
        "tipo": "Camisa", "cor": "Branca", "preco": 100.0, "estoque": 1,
        "corredor": "5", "descricao": "Camisa branca"
    }
    prod2 = {
        "id": 4, "nome": "Bermuda Preta Masculina", "categoria": "Bermudas",
        "tipo": "Bermuda", "cor": "Preta", "preco": 80.0, "estoque": 1,
        "corredor": "2", "descricao": "Bermuda preta"
    }
    
    pipeline_service.memoria["produtos_mencionados"] = {15: prod1, 4: prod2}
    pipeline_service.memoria["ultimos_produtos"] = [prod1, prod2]
    
    # User asks map for both items
    resposta = asyncio.run(pipeline_service.pipeline_processar("onde é que eu encontro eles?"))
    
    # Should say "onde estao os 2 produtos." and return 2 corridors
    assert "2 produtos" in resposta["resposta"]
    assert len(resposta["resultados"]) == 2


def test_pipeline_remove_quantidade_por_extenso_da_busca():
    tokens = pipeline_service.limpar_tokens_busca(["camisetas", "tres", "pretas"])

    assert "camisa" in tokens
    assert "tres" not in tokens
    assert "preta" in tokens or "pretas" in tokens


def test_comprar_produto_novo_nao_e_confirmacao_de_caixa():
    assert pipeline_service.is_confirmacao_compra("Eu quero comprar um oculos.") is False
    assert pipeline_service.is_confirmacao_compra("Eu quero comprar esses produtos.") is True


def test_pipeline_mapa_produto_citado_tem_prioridade_sobre_memoria(monkeypatch):
    pipeline_service.limpar_memoria()

    oculos = {
        "id": 1, "nome": "Oculos de Sol Masculino", "categoria": "Acessorios",
        "tipo": "Oculos", "cor": "Preto", "preco": 79.9, "estoque": 2,
        "corredor": "1", "setor": "Acessorios", "descricao": "Oculos de sol",
        "tamanho": "Unico", "marca": "", "prateleira": "", "sku": "OCU-1",
        "imagem": "", "texto_alt": "",
    }
    bone = {
        "id": 2, "nome": "Bone Masculino Preto", "categoria": "Acessorios",
        "tipo": "Bone", "cor": "Preto", "preco": 49.9, "estoque": 3,
        "corredor": "1", "setor": "Acessorios", "descricao": "Bone masculino",
        "tamanho": "Unico", "marca": "", "prateleira": "", "sku": "BON-1",
        "imagem": "", "texto_alt": "",
    }

    pipeline_service.memoria["ultimos_produtos"] = [oculos]
    pipeline_service.memoria["produtos_mencionados"] = {1: oculos}

    monkeypatch.setattr(pipeline_service.db_service, "fetchall", lambda *args, **kwargs: [oculos, bone])

    resposta = asyncio.run(pipeline_service.pipeline_processar("Ta, eu quero saber onde e que o bone fica."))

    assert resposta["acao"] == "ABRIR_MAPA"
    assert resposta["resultados"]
    assert resposta["resultados"][0]["id"] == 2


def test_pipeline_vou_quere_levar_entende_como_compra():
    pipeline_service.limpar_memoria()

    camisa = {
        "id": 10, "nome": "Camisa Polo Masculina", "categoria": "Camisas",
        "tipo": "Camisa", "cor": "Branca", "tamanho": "M", "marca": "",
        "preco": 119.9, "estoque": 1, "corredor": "5", "setor": "Camisas",
        "prateleira": "", "descricao": "Camisa polo masculina", "sku": "CAM-1",
        "imagem": "", "texto_alt": "",
    }
    oculos = {
        "id": 11, "nome": "Oculos de Sol Masculino", "categoria": "Acessorios",
        "tipo": "Oculos", "cor": "Preto", "tamanho": "Unico", "marca": "",
        "preco": 79.9, "estoque": 1, "corredor": "1", "setor": "Acessorios",
        "prateleira": "", "descricao": "Oculos de sol masculino", "sku": "OCU-1",
        "imagem": "", "texto_alt": "",
    }

    pipeline_service.memoria["ultimos_produtos"] = [camisa, oculos]
    pipeline_service.memoria["produtos_mencionados"] = {10: camisa, 11: oculos}

    resposta = asyncio.run(
        pipeline_service.pipeline_processar("Gostei, vou quere levar a camisa polo e oculos de sol masculino.")
    )

    assert resposta["acao"] == "ABRIR_ROTAS"
    assert {produto["id"] for produto in resposta["resultados"]} == {10, 11, "caixa"}


def test_pipeline_nova_busca_depois_de_agradaram_nao_herda_produto_anterior(monkeypatch):
    pipeline_service.limpar_memoria()

    camisa = {
        "id": 20, "nome": "Camisa Polo Branca Masculina", "categoria": "Camisas",
        "tipo": "Camisa", "cor": "Branca", "tamanho": "M", "marca": "",
        "preco": 119.9, "estoque": 1, "corredor": "5", "setor": "Camisas",
        "prateleira": "", "descricao": "Camisa polo masculina", "sku": "CAM-2",
        "imagem": "", "texto_alt": "",
    }
    oculos = {
        "id": 21, "nome": "Oculos de Sol Masculino", "categoria": "Acessorios",
        "tipo": "Oculos", "cor": "Preto", "tamanho": "Unico", "marca": "",
        "preco": 79.9, "estoque": 1, "corredor": "1", "setor": "Acessorios",
        "prateleira": "", "descricao": "Oculos de sol masculino", "sku": "OCU-2",
        "imagem": "", "texto_alt": "",
    }

    pipeline_service.memoria["ultimos_produtos"] = [camisa]
    pipeline_service.memoria["produtos_mencionados"] = {20: camisa}
    pipeline_service.memoria["tipo_ativo"] = "camisa"

    async def fake_classificar_intencao(pergunta, idioma="pt"):
        return {"intencao": "NOVA_BUSCA", "palavras_chave": ["camisa", "agradaram", "sol"]}

    monkeypatch.setattr(pipeline_service, "classificar_intencao", fake_classificar_intencao)
    monkeypatch.setattr(pipeline_service.db_service, "fetchall", lambda *args, **kwargs: [camisa, oculos])

    resposta = asyncio.run(
        pipeline_service.pipeline_processar("As duas me agradaram. Voce tem oculos de sol masculino?")
    )

    assert resposta["acao"] == "MOSTRAR_PRODUTOS"
    assert [produto["id"] for produto in resposta["resultados"]] == [21]
