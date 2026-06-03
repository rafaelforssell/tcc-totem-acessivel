import unicodedata

from services.db_service import fetchall


def obter_campo(produto, campo, indice=None, padrao=""):
    try:
        return produto[campo]
    except (IndexError, KeyError, TypeError):
        if indice is None:
            return padrao
        return produto[indice] if len(produto) > indice else padrao


def normalizar_texto(texto):
    sem_acento = unicodedata.normalize("NFKD", texto or "")
    return "".join(ch for ch in sem_acento if not unicodedata.combining(ch)).lower()


def produto_contem_termos(produto, termo):
    texto_produto = " ".join(
        str(obter_campo(produto, campo))
        for campo in ["nome", "categoria", "tipo", "cor", "marca", "descricao", "sku"]
    ).replace("_", " ")
    palavras = normalizar_texto(termo).replace("_", " ").split()
    return all(palavra in normalizar_texto(texto_produto) for palavra in palavras)


def formatar_produto(produto):
    imagem_1 = obter_campo(produto, "imagem")

    return {
        "id": obter_campo(produto, "id", 0),
        "sku": obter_campo(produto, "sku"),
        "nome": obter_campo(produto, "nome", 1),
        "categoria": obter_campo(produto, "categoria", 2),
        "tipo": obter_campo(produto, "tipo", 3),
        "cor": obter_campo(produto, "cor", 4),
        "tamanho": obter_campo(produto, "tamanho", 5),
        "marca": obter_campo(produto, "marca", 6),
        "preco": obter_campo(produto, "preco", 7, 0),
        "estoque": obter_campo(produto, "estoque", 8, 0),
        "setor": obter_campo(produto, "setor", 9),
        "corredor": obter_campo(produto, "corredor", 10),
        "prateleira": obter_campo(produto, "prateleira", 11),
        "descricao": obter_campo(produto, "descricao", 12),
        "imagem": imagem_1,
        "texto_alt": obter_campo(produto, "texto_alt"),
    }


def listar_produtos_db():
    produtos = fetchall("SELECT * FROM produtos ORDER BY nome, cor, tamanho")
    return {"produtos": [formatar_produto(p) for p in produtos]}


def buscar_produto_db(nome):
    termo = (nome or "").strip()
    if not termo:
        return {"resultado": []}

    produtos = fetchall("SELECT * FROM produtos ORDER BY nome, cor, tamanho")
    produtos = [p for p in produtos if produto_contem_termos(p, termo)]

    if produtos:
        return {"resultado": [formatar_produto(p) for p in produtos]}

    produtos = fetchall(
        """
        SELECT * FROM produtos
        WHERE nome LIKE ?
           OR categoria LIKE ?
           OR tipo LIKE ?
           OR cor LIKE ?
           OR marca LIKE ?
           OR descricao LIKE ?
           OR sku LIKE ?
        ORDER BY nome, cor, tamanho
        """,
        tuple(f"%{termo}%" for _ in range(7)),
    )

    return {"resultado": [formatar_produto(p) for p in produtos]}


def contar_produtos_db():
    resultado = fetchall("SELECT COUNT(*) AS total FROM produtos")
    return resultado[0]["total"] if resultado else 0
