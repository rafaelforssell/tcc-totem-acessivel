from services.produtos_service import buscar_produto_db, contar_produtos_db, listar_produtos_db


def test_lista_produtos_com_schema_completo():
    resposta = listar_produtos_db()

    assert "produtos" in resposta
    assert resposta["produtos"]
    produto = resposta["produtos"][0]
    assert {
        "id",
        "nome",
        "categoria",
        "tipo",
        "cor",
        "tamanho",
        "marca",
        "preco",
        "estoque",
        "setor",
        "corredor",
        "prateleira",
        "descricao",
        "imagem",
    }.issubset(produto)


def test_busca_produto_por_nome_retorna_camisa():
    resposta = buscar_produto_db("camisa")

    assert resposta["resultado"]
    assert any("camisa" in produto["nome"].lower() for produto in resposta["resultado"])


def test_busca_vazia_nao_retorna_catalogo_inteiro():
    assert buscar_produto_db("") == {"resultado": []}


def test_imagem_de_produto_nao_usa_comida():
    produto = buscar_produto_db("camiseta")["resultado"][0]

    assert "images.unsplash.com" in produto["imagem"]
    assert "prezunic" not in produto["imagem"]


def test_contador_de_produtos():
    assert contar_produtos_db() >= 1
