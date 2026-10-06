from contextlib import asynccontextmanager
from datetime import datetime, timezone
import os
import sqlite3

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routes import produtos, query, admin, atendente
from services.llm_service import perguntar_llm
from services.produtos_service import buscar_produto_db, contar_produtos_db
from services import db_service


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
AUDIO_DIR = os.path.join(BASE_DIR, "audios")
ASSETS_DIR = os.path.join(PROJECT_DIR, "assets")
os.makedirs(AUDIO_DIR, exist_ok=True)

SQLITE_PATH = os.path.join(PROJECT_DIR, "database", "produtos.db")


def _auto_init_postgres():
    """Cria a tabela e migra dados do SQLite para o PostgreSQL no primeiro boot."""
    if not db_service.usando_postgres():
        print("[DB] Usando SQLite local.")
        return

    print("[DB] PostgreSQL detectado. Verificando tabela...")
    try:
        import psycopg2
        DATABASE_URL = os.getenv("DATABASE_URL", "").replace("postgres://", "postgresql://", 1)
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        # Cria tabela se não existir
        cur.execute("""
            CREATE TABLE IF NOT EXISTS produtos (
                id SERIAL PRIMARY KEY,
                nome TEXT, categoria TEXT, tipo TEXT, cor TEXT,
                tamanho TEXT, marca TEXT, preco REAL, estoque INTEGER DEFAULT 1,
                setor TEXT, corredor TEXT, prateleira TEXT, descricao TEXT,
                sku TEXT UNIQUE, imagem TEXT, imagem_2 TEXT,
                imagem_3 TEXT, imagem_4 TEXT, texto_alt TEXT
            )
        """)
        conn.commit()

        # Garante que colunas novas como 'tamanho' existam (caso a tabela já existisse antes)
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'produtos'")
        columns = [row[0] for row in cur.fetchall()]
        if "tamanho" not in columns:
            print("[DB] Adicionando coluna 'tamanho' ao PostgreSQL...")
            cur.execute("ALTER TABLE produtos ADD COLUMN tamanho TEXT")
            conn.commit()

        # Verifica se já tem dados
        cur.execute("SELECT COUNT(*) FROM produtos")
        total = cur.fetchone()[0]

        if total == 0 and os.path.exists(SQLITE_PATH):
            print(f"[DB] Tabela vazia. Migrando dados do SQLite ({SQLITE_PATH})...")
            sq = sqlite3.connect(SQLITE_PATH)
            sq.row_factory = sqlite3.Row
            rows = sq.execute("SELECT * FROM produtos").fetchall()
            sq.close()

            for row in rows:
                try:
                    cur.execute("""
                        INSERT INTO produtos (
                            id, nome, categoria, tipo, cor, tamanho, marca, preco, estoque,
                            setor, corredor, prateleira, descricao, sku, imagem,
                            imagem_2, imagem_3, imagem_4, texto_alt
                        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (sku) DO NOTHING
                    """, (
                        row["id"], row["nome"], row["categoria"], row["tipo"],
                        row["cor"], row["tamanho"], row["marca"], row["preco"],
                        row["estoque"], row["setor"], row["corredor"], row["prateleira"],
                        row["descricao"], row["sku"], row["imagem"],
                        row["imagem_2"] if "imagem_2" in row.keys() else "",
                        row["imagem_3"] if "imagem_3" in row.keys() else "",
                        row["imagem_4"] if "imagem_4" in row.keys() else "",
                        row["texto_alt"] if "texto_alt" in row.keys() else "",
                    ))
                except Exception as e:
                    print(f"  [DB] Erro no produto {row['sku']}: {e}")
            conn.commit()
            cur.execute("SELECT COUNT(*) FROM produtos")
            print(f"[DB] Migração concluída: {cur.fetchone()[0]} produtos no PostgreSQL.")
        else:
            print(f"[DB] PostgreSQL já tem {total} produtos. Nenhuma migração necessária.")

        # Sincroniza a sequence do ID para evitar conflito de ID duplicado em novos inserts
        cur.execute("SELECT setval('produtos_id_seq', COALESCE((SELECT MAX(id) FROM produtos), 1))")
        conn.commit()

        conn.close()
    except Exception as e:
        print(f"[DB] Erro na inicialização do PostgreSQL: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _auto_init_postgres()
    yield


app = FastAPI(title="Totem Acessivel API", lifespan=lifespan)
app.mount("/audios", StaticFiles(directory=AUDIO_DIR), name="audios")
app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")

# Origens autorizadas: o frontend publicado e, para desenvolvimento, qualquer porta do localhost.
# CORS_ORIGINS (lista separada por virgula) substitui o dominio padrao, se definida.
FRONTEND_PADRAO = "https://totem-acessiveltcc.netlify.app"
CORS_ORIGINS = [o.strip() for o in (os.getenv("CORS_ORIGINS") or FRONTEND_PADRAO).split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "X-Admin-Key", "X-Session-Id"],
)

app.include_router(query.router)
app.include_router(produtos.router)
app.include_router(admin.router)
app.include_router(atendente.router)


@app.get("/")
def home():
    return {"mensagem": "Totem funcionando"}


@app.post("/reset")
def reset_session(x_session_id: str | None = Header(default=None)):
    from services.pipeline_service import limpar_memoria
    # Limpa apenas a sessao de quem chamou, nunca a de outros totens
    limpar_memoria(x_session_id or "")
    return {"status": "success", "mensagem": "Memória limpa"}



@app.get("/health")
def health():
    try:
        total_produtos = contar_produtos_db()
    except Exception as exc:
        # O detalhe do erro fica so no log do servidor, nunca na resposta publica
        print(f"[HEALTH] Falha ao acessar o banco: {exc}")
        raise HTTPException(status_code=503, detail={"status": "erro", "db": "indisponivel"})

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
