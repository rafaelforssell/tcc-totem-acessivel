import sqlite3
import os
import sys

DB_PATH = "database/produtos.db"

def check(query=""):
    if not os.path.exists(DB_PATH):
        print("DB not found")
        return
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if query:
        cursor.execute(f"SELECT * FROM produtos WHERE nome LIKE ?", (f"%{query}%",))
    else:
        cursor.execute("SELECT * FROM produtos LIMIT 10")
    rows = cursor.fetchall()
    print(f"Found {len(rows)} products")
    for r in rows:
        print(r)
    conn.close()

if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else ""
    check(q)
