"""
Script de inicialização do PostgreSQL.
Cria a tabela 'produtos' e importa os dados do SQLite local.

Uso:
    DATABASE_URL=postgresql://... python database/init_postgres.py

Ou com o SQLite já populado localmente, este script migra todos os dados.
"""
import os
import sys
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SQLITE_PATH = BASE_DIR / "produtos.db"


def main():
    database_url = os.getenv("DATABASE_URL", "")
    if not database_url:
        print("❌ Variável DATABASE_URL não encontrada.")
        sys.exit(1)

    # Render usa postgres://, psycopg2 precisa de postgresql://
    database_url = database_url.replace("postgres://", "postgresql://", 1)

    try:
        import psycopg2
    except ImportError:
        print("❌ psycopg2 não instalado. Execute: pip install psycopg2-binary")
        sys.exit(1)

    print(f"🔌 Conectando ao PostgreSQL...")
    pg_conn = psycopg2.connect(database_url)
    pg_cur = pg_conn.cursor()

    # Cria tabela
    pg_cur.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id SERIAL PRIMARY KEY,
            nome TEXT,
            categoria TEXT,
            tipo TEXT,
            cor TEXT,
            tamanho TEXT,
            marca TEXT,
            preco REAL,
            estoque INTEGER DEFAULT 1,
            setor TEXT,
            corredor TEXT,
            prateleira TEXT,
            descricao TEXT,
            sku TEXT UNIQUE,
            imagem TEXT,
            imagem_2 TEXT,
            imagem_3 TEXT,
            imagem_4 TEXT,
            texto_alt TEXT
        )
    """)
    pg_conn.commit()
    print("✅ Tabela 'produtos' criada/verificada.")

    if not SQLITE_PATH.exists():
        print(f"⚠️  SQLite não encontrado em {SQLITE_PATH}. Tabela criada vazia.")
        pg_conn.close()
        return

    # Importa dados do SQLite
    print(f"📦 Importando dados do SQLite ({SQLITE_PATH})...")
    sq_conn = sqlite3.connect(SQLITE_PATH)
    sq_conn.row_factory = sqlite3.Row
    sq_cur = sq_conn.cursor()
    sq_cur.execute("SELECT * FROM produtos")
    rows = sq_cur.fetchall()
    sq_conn.close()

    if not rows:
        print("⚠️  Nenhum produto no SQLite para importar.")
        pg_conn.close()
        return

    inseridos = 0
    ignorados = 0
    for row in rows:
        try:
            pg_cur.execute("""
                INSERT INTO produtos (
                    id, nome, categoria, tipo, cor, tamanho, marca, preco, estoque,
                    setor, corredor, prateleira, descricao, sku, imagem,
                    imagem_2, imagem_3, imagem_4, texto_alt
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (sku) DO UPDATE SET
                    estoque = EXCLUDED.estoque,
                    preco = EXCLUDED.preco,
                    nome = EXCLUDED.nome
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
            inseridos += 1
        except Exception as e:
            print(f"  ⚠️  Erro no produto {row['sku']}: {e}")
            ignorados += 1

    pg_conn.commit()
    pg_conn.close()
    print(f"✅ Importação concluída: {inseridos} inseridos, {ignorados} ignorados.")


if __name__ == "__main__":
    main()
