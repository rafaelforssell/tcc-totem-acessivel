from fastapi import FastAPI
from routes import query
from fastapi.middleware.cors import CORSMiddleware
from services.llm_service import perguntar_llm
from fastapi.staticfiles import StaticFiles
import sqlite3
import os

app = FastAPI()
app.mount("/audios", StaticFiles(directory="audios"), name="audios")

# CORS (tem que vir antes das rotas)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # permite qualquer origem (ok para TCC)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(query.router)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "database", "produtos.db")

def conectar_bd():
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

@app.get("/")
def home():
    return {"mensagem": "Totem funcionando"}

@app.get("/produtos")
def listar_produtos():
    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM produtos")
    produtos = cursor.fetchall()

    conn.close()

    produtos_formatados = [formatar_produto(produto) for produto in produtos]

    return {"produtos": produtos_formatados}

@app.get("/buscar-produto")
def buscar_produto(nome: str):
    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM produtos WHERE nome LIKE ?", ('%' + nome + '%',))
    produtos = cursor.fetchall()

    conn.close()

    produtos_formatados = [formatar_produto(produto) for produto in produtos]

    return {"resultado": produtos_formatados}

@app.get("/perguntar-ia")
async def perguntar_ia(pergunta: str):
    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM produtos WHERE nome LIKE ?",
        ('%' + pergunta + '%',)
    )

    produtos = cursor.fetchall()
    conn.close()

    if not produtos:
        contexto = "Nenhum produto encontrado."
    else:
        linhas = []
        for p in produtos:
            linhas.append(
                f"Nome: {p[1]} | Categoria: {p[2]} | Preço: {p[3]} | Descrição: {p[4]} | Estoque: {p[5]}"
            )

        contexto = "\n".join(linhas)

    resposta = await perguntar_llm(pergunta, contexto)

    return {
        "pergunta": pergunta,
        "resposta": resposta
    }