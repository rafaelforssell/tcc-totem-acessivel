import sqlite3
import unicodedata

def normalizar_texto(texto):
    if not texto:
        return ""
    sem_acento = unicodedata.normalize("NFKD", texto)
    return "".join(ch for ch in sem_acento if not unicodedata.combining(ch)).lower()

def run():
    conn = sqlite3.connect('database/produtos.db')
    cur = conn.cursor()
    cur.execute('SELECT id, nome, categoria, tipo FROM produtos')
    rows = cur.fetchall()

    for row in rows:
        p_id, nome, categoria, tipo = row
        nome_norm = normalizar_texto(nome)
        cat_norm = normalizar_texto(categoria)
        tipo_norm = normalizar_texto(tipo)
        
        combined = f"{nome_norm} {cat_norm} {tipo_norm}"
        
        if any(k in combined for k in ["tenis", "sandalia", "sapato", "calcado", "calcados"]):
            tamanho = "36, 37, 38, 39, 40, 41, 42"
        elif any(k in combined for k in ["bone", "oculos", "cinto", "garrafa", "touca"]):
            tamanho = "Único"
        else:
            tamanho = "P, M, G, GG"
            
        cur.execute("UPDATE produtos SET tamanho = ? WHERE id = ?", (tamanho, p_id))

    conn.commit()
    conn.close()
    print("Migration completed with normalization!")

if __name__ == "__main__":
    run()
