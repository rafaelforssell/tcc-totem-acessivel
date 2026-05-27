"""
Serviço de conexão ao banco de dados.
Prioriza PostgreSQL (DATABASE_URL) e cai para SQLite como fallback local.
"""
import os
import sqlite3
from contextlib import contextmanager
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, "..", ".env")
load_dotenv(ENV_PATH)

DATABASE_URL = os.getenv("DATABASE_URL")
SQLITE_PATH = os.path.join(BASE_DIR, "..", "..", "database", "produtos.db")

_usando_postgres = False

# Tenta importar psycopg2 (PostgreSQL)
try:
    import psycopg2
    import psycopg2.extras
    _psycopg2_disponivel = True
except ImportError:
    _psycopg2_disponivel = False


def usando_postgres() -> bool:
    return bool(DATABASE_URL and _psycopg2_disponivel)


@contextmanager
def get_conn():
    """Context manager que retorna uma conexão ao banco correto. Cai para SQLite em caso de falha."""
    if usando_postgres():
        try:
            # Render fornece URLs com "postgres://", psycopg2 exige "postgresql://"
            url = DATABASE_URL.replace("postgres://", "postgresql://", 1)
            conn = psycopg2.connect(url, connect_timeout=5)
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()
            return  # Conexão PostgreSQL bem sucedida
        except Exception as e:
            print(f"[DB] Erro de conexão com o PostgreSQL, caindo para SQLite: {e}")

    # Fallback para SQLite
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def fetchall(query: str, params=()) -> list[dict]:
    """Executa SELECT e retorna lista de dicts."""
    with get_conn() as conn:
        if isinstance(conn, sqlite3.Connection):
            cur = conn.cursor()
            cur.execute(query, params)
            rows = cur.fetchall()
            if rows:
                cols = [d[0] for d in cur.description]
                return [dict(zip(cols, row)) for row in rows]
            return []
        else:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            # SQLite usa ? como placeholder, PostgreSQL usa %s
            pg_query = query.replace("?", "%s")
            cur.execute(pg_query, params)
            return [dict(row) for row in cur.fetchall()]


def fetchone(query: str, params=()) -> dict | None:
    """Executa SELECT e retorna um dict ou None."""
    results = fetchall(query, params)
    return results[0] if results else None


def execute(query: str, params=()) -> int:
    """Executa INSERT/UPDATE/DELETE e retorna rowcount."""
    with get_conn() as conn:
        if isinstance(conn, sqlite3.Connection):
            cur = conn.cursor()
            cur.execute(query, params)
            return cur.rowcount
        else:
            pg_query = query.replace("?", "%s")
            cur = conn.cursor()
            cur.execute(pg_query, params)
            return cur.rowcount


def executemany(query: str, params_list) -> None:
    """Executa INSERT/UPDATE em batch."""
    with get_conn() as conn:
        if isinstance(conn, sqlite3.Connection):
            cur = conn.cursor()
            cur.executemany(query, params_list)
        else:
            pg_query = query.replace("?", "%s")
            cur = conn.cursor()
            cur.executemany(pg_query, params_list)

