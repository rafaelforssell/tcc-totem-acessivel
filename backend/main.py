from datetime import datetime, timezone
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routes import produtos, query
from services.llm_service import perguntar_llm
from services.produtos_service import buscar_produto_db, contar_produtos_db


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
AUDIO_DIR = os.path.join(BASE_DIR, "audios")
ASSETS_DIR = os.path.join(PROJECT_DIR, "assets")
os.makedirs(AUDIO_DIR, exist_ok=True)

app = FastAPI(title="Totem Acessivel API")
app.mount("/audios", StaticFiles(directory=AUDIO_DIR), name="audios")
app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # suficiente para a demonstracao academica
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query.router)
app.include_router(produtos.router)


@app.get("/")
def home():
    return {"mensagem": "Totem funcionando"}


@app.post("/reset")
def reset_session():
    from services.pipeline_service import limpar_memoria
    limpar_memoria()
    return {"status": "success", "mensagem": "Memória limpa"}



@app.get("/health")
def health():
    try:
        total_produtos = contar_produtos_db()
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={"status": "erro", "db": "indisponivel", "erro": str(exc)},
        )

    return {
        "status": "ok",
        "db": "ok",
        "produtos": total_produtos,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/perguntar-ia")
async def perguntar_ia(pergunta: str):
    produtos_encontrados = buscar_produto_db(pergunta)["resultado"]

    if not produtos_encontrados:
        contexto = "Nenhum produto encontrado."
    else:
        linhas = []
        for produto in produtos_encontrados:
            linhas.append(
                f"Nome: {produto['nome']} | Categoria: {produto['categoria']} | "
                f"Preco: {produto['preco']} | Descricao: {produto['descricao']} | "
                f"Estoque: {produto['estoque']}"
            )
        contexto = "\n".join(linhas)

    resposta = await perguntar_llm(pergunta, contexto)

    return {
        "pergunta": pergunta,
        "resposta": resposta,
    }
