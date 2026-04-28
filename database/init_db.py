import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "produtos.db")

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
    # MASCULINO
    ("Camiseta Básica", "Roupa", "Camiseta", "Preta", "M", "Hering", 49.90, 15, "Masculino", "1", "Arara 1", "Camiseta 100% algodão"),
    ("Camiseta Básica", "Roupa", "Camiseta", "Branca", "G", "Hering", 49.90, 12, "Masculino", "1", "Arara 1", "Camiseta 100% algodão"),
    ("Calça Jeans Slim", "Roupa", "Calça", "Azul", "42", "Levi's", 199.90, 8, "Masculino", "2", "Prateleira 1", "Calça jeans com elastano"),
    ("Jaqueta de Couro", "Roupa", "Jaqueta", "Preta", "G", "Zara", 359.90, 3, "Masculino", "3", "Arara 2", "Jaqueta de couro sintético"),
    ("Bermuda Sarja", "Roupa", "Bermuda", "Cáqui", "40", "Renner", 89.90, 10, "Masculino", "2", "Prateleira 2", "Bermuda de sarja confortável"),
    ("Camisa Polo", "Roupa", "Polo", "Azul Marinho", "M", "Lacoste", 249.90, 5, "Masculino", "1", "Arara 3", "Polo clássica"),

    # FEMININO
    ("Vestido Floral", "Roupa", "Vestido", "Vermelho/Branco", "M", "Farm", 289.90, 6, "Feminino", "4", "Arara 4", "Vestido longo de viscose"),
    ("Blusa Tricô", "Roupa", "Blusa", "Rosa", "P", "Zara", 129.90, 8, "Feminino", "5", "Prateleira 3", "Blusa de tricô leve"),
    ("Calça Pantalona", "Roupa", "Calça", "Preta", "38", "Renner", 149.90, 10, "Feminino", "4", "Arara 5", "Calça de alfaiataria"),
    ("Saia Midi Plissada", "Roupa", "Saia", "Verde", "M", "Amaro", 119.90, 4, "Feminino", "4", "Prateleira 4", "Saia elegante plissada"),
    ("Jaqueta Jeans", "Roupa", "Jaqueta", "Azul Claro", "M", "Levi's", 259.90, 5, "Feminino", "5", "Arara 6", "Jaqueta jeans clássica"),
    ("Cropped Básico", "Roupa", "Cropped", "Branco", "P", "Hering", 39.90, 20, "Feminino", "4", "Arara 7", "Cropped canelado"),

    # ESPORTIVO
    ("Legging Academia", "Roupa", "Legging", "Preta", "M", "Nike", 129.90, 15, "Esportivo", "6", "Arara 8", "Legging cintura alta"),
    ("Top Fit", "Roupa", "Top", "Rosa", "P", "Adidas", 89.90, 12, "Esportivo", "6", "Arara 8", "Top com alta sustentação"),
    ("Camisa Dry Fit", "Roupa", "Treino", "Preta", "GG", "Nike", 79.90, 8, "Esportivo", "7", "Arara 9", "Camisa esportiva respirável"),
    ("Bermuda Running", "Roupa", "Treino", "Cinza", "G", "Adidas", 89.90, 5, "Esportivo", "7", "Arara 9", "Bermuda leve esportiva")
]

cursor.executemany("""
INSERT INTO produtos (
nome, categoria, tipo, cor, tamanho, marca,
preco, estoque, setor, corredor, prateleira, descricao
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", produtos)

conn.commit()
conn.close()

print("Banco profissional criado com sucesso.")