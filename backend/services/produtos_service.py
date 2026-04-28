import sqlite3
import os

def conectar_bd():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, "..", "..", "database", "produtos.db")

    return sqlite3.connect(DB_PATH)

def formatar_produto(produto):
    return {
        "id": produto[0],
        "nome": produto[1],
        "categoria": produto[2],
        "preco": produto[3],
        "descricao": produto[4],
        "estoque": produto[5]
    }

def buscar_produtos_por_nome(nome):
    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM produtos 
        WHERE nome LIKE ? OR categoria LIKE ?
    """, (f"%{nome}%", f"%{nome}%"))

    produtos = cursor.fetchall()
    conn.close()

    return [formatar_produto(p) for p in produtos]