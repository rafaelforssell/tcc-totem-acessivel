import sqlite3
import os

DB_PATH = "produtos.db"

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    categoria TEXT,
    tipo TEXT,
    cor TEXT,
    tamanho TEXT,
    marca TEXT,
    preco REAL,
    estoque INTEGER,
    setor TEXT,
    corredor TEXT,
    prateleira TEXT,
    descricao TEXT
)
""")

produtos = [

("Camisa Dry Fit", "Roupa", "Treino", "Preta", "GG", "Nike", 79.90, 8, "Esportivo", "2", "Arara 4", "Camisa esportiva"),
("Camisa Dry Fit", "Roupa", "Treino", "Azul", "GG", "Nike", 79.90, 6, "Esportivo", "2", "Arara 4", "Camisa esportiva"),
("Arroz 5kg", "Alimento", "Arroz", "Branco", "5kg", "Camil", 28.90, 15, "Mercearia", "3", "Prateleira 2", "Arroz tipo 1"),
("Feijão Carioca 1kg", "Alimento", "Feijão", "Bege", "1kg", "Kicaldo", 8.90, 22, "Mercearia", "3", "Prateleira 3", "Feijão carioca"),
("Café 500g", "Alimento", "Café", "N/A", "500g", "Pilão", 16.90, 19, "Mercearia", "4", "Prateleira 1", "Café torrado")

]

cursor.executemany("""
INSERT INTO produtos (
nome,categoria,tipo,cor,tamanho,marca,
preco,estoque,setor,corredor,prateleira,descricao
)
VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
""", produtos)

conn.commit()
conn.close()

print("Banco criado com sucesso.")