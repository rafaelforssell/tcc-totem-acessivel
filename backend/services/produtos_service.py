import os
import sqlite3


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "..", "database", "produtos.db")
CLOTHING_IMAGES = {
    "camiseta": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=500&q=80",
    "camisa": "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?auto=format&fit=crop&w=500&q=80",
    "calca": "https://images.unsplash.com/photo-1542272604-787c3835535d?auto=format&fit=crop&w=500&q=80",
    "jaqueta": "https://images.unsplash.com/photo-1551028719-00167b16eac5?auto=format&fit=crop&w=500&q=80",
    "vestido": "https://images.unsplash.com/photo-1595777457583-95e059d581b8?auto=format&fit=crop&w=500&q=80",
    "blusa": "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?auto=format&fit=crop&w=500&q=80",
    "bermuda": "https://images.unsplash.com/photo-1591195853828-11db59a44f6b?auto=format&fit=crop&w=500&q=80",
    "legging": "https://images.unsplash.com/photo-1506629905607-d9d297d644c0?auto=format&fit=crop&w=500&q=80",
    "default": "https://images.unsplash.com/photo-1445205170230-053b83016050?auto=format&fit=crop&w=500&q=80",
}


def conectar_bd():
    return sqlite3.connect(DB_PATH)


def normalizar_texto(texto):
    return (
        texto.lower()
        .replace("á", "a")
        .replace("ã", "a")
        .replace("â", "a")
        .replace("é", "e")
        .replace("ê", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ô", "o")
        .replace("ú", "u")
        .replace("ç", "c")
    )


def escolher_imagem_produto(nome, tipo):
    texto = normalizar_texto(f"{nome} {tipo}")
    for chave, imagem in CLOTHING_IMAGES.items():
        if chave != "default" and chave in texto:
            return imagem
    return CLOTHING_IMAGES["default"]


def formatar_produto(produto):
    return {
        "id": produto[0],
        "nome": produto[1],
        "categoria": produto[2],
        "tipo": produto[3],
        "cor": produto[4],
        "tamanho": produto[5],
        "marca": produto[6],
        "preco": produto[7],
        "estoque": produto[8],
        "setor": produto[9],
        "corredor": produto[10],
        "prateleira": produto[11],
        "descricao": produto[12],
        "imagem": escolher_imagem_produto(produto[1], produto[3]),
    }


def listar_produtos_db():
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM produtos ORDER BY nome, cor, tamanho")
    produtos = cursor.fetchall()
    conn.close()

    return {"produtos": [formatar_produto(p) for p in produtos]}


def buscar_produto_db(nome):
    termo = (nome or "").strip()
    if not termo:
        return {"resultado": []}

    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM produtos
        WHERE nome LIKE ?
           OR categoria LIKE ?
           OR tipo LIKE ?
           OR cor LIKE ?
           OR marca LIKE ?
           OR descricao LIKE ?
        ORDER BY nome, cor, tamanho
        """,
        tuple(f"%{termo}%" for _ in range(6)),
    )
    produtos = cursor.fetchall()
    conn.close()

    return {"resultado": [formatar_produto(p) for p in produtos]}


def contar_produtos_db():
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM produtos")
    total = cursor.fetchone()[0]
    conn.close()
    return total
