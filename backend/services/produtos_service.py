import os
import sqlite3


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "..", "database", "produtos.db")


def conectar_bd():
    return sqlite3.connect(DB_PATH)


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
