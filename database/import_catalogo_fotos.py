import os
import sqlite3
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
DEFAULT_XLSX = Path.home() / "Desktop" / "Banco de fotos totem.xlsx"
IMAGE_BASE_URL = "/assets/imagens/produtos"
IMAGE_DIR = PROJECT_DIR / "assets" / "imagens" / "produtos"
DB_PATH = BASE_DIR / "produtos.db"

NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def read_xml(zip_file, name):
    return ET.fromstring(zip_file.read(name))


def shared_strings(zip_file):
    try:
        root = read_xml(zip_file, "xl/sharedStrings.xml")
    except KeyError:
        return []
    values = []
    for si in root.findall("a:si", NS):
        values.append("".join(t.text or "" for t in si.findall(".//a:t", NS)))
    return values


def rows_from_xlsx(path):
    with zipfile.ZipFile(path) as zip_file:
        strings = shared_strings(zip_file)
        sheet = read_xml(zip_file, "xl/worksheets/sheet1.xml")
        rows = []
        for row in sheet.findall(".//a:sheetData/a:row", NS):
            values = {}
            for cell in row.findall("a:c", NS):
                ref = cell.attrib["r"]
                column = "".join(ch for ch in ref if ch.isalpha())
                value = cell.find("a:v", NS)
                if value is None or value.text is None:
                    continue
                if cell.attrib.get("t") == "s":
                    values[column] = strings[int(value.text)]
                else:
                    raw = value.text
                    values[column] = str(int(float(raw))) if raw.endswith(".0") else raw
            rows.append(values)

        headers = rows[0]
        for row in rows[1:]:
            product = {
                headers.get(column, column): value
                for column, value in row.items()
                if headers.get(column) and value
            }
            if product.get("SKU") and product.get("Nome do Produto"):
                yield product


def tipo_from_nome(nome):
    return nome.split()[0] if nome else ""


def cor_from_nome(nome):
    cores = [
        "Bege",
        "Jeans",
        "Preta",
        "Preto",
        "Azul",
        "Branco",
        "Branca",
        "Marrom",
        "Cinza",
        "Verde",
        "Vermelho",
        "Xadrez",
    ]
    for cor in cores:
        if cor.lower() in nome.lower():
            return cor
    return ""


def corredor_from_categoria(categoria):
    corredores = {
        "Acessórios": "1",
        "Bermudas": "2",
        "Calçados": "3",
        "Calças": "4",
        "Camisas": "5",
        "Casacos": "6",
        "Saias e Vestidos": "7",
    }
    return corredores.get(categoria, "1")


def preco_from_produto(nome, categoria):
    nome_baixo = nome.lower()
    precos_tipo = {
        "boné": 49.90,
        "cinto": 39.90,
        "garrafa": 59.90,
        "óculos": 79.90,
        "touca": 34.90,
        "bermuda": 89.90,
        "calça": 159.90,
        "camisa": 119.90,
        "polo": 139.90,
        "casaco": 229.90,
        "moletom": 179.90,
        "saia": 99.90,
        "sandália": 129.90,
        "tênis": 249.90,
        "vestido": 189.90,
    }
    for tipo, preco in precos_tipo.items():
        if tipo in nome_baixo:
            return preco

    precos_categoria = {
        "Acessórios": 59.90,
        "Bermudas": 89.90,
        "Calçados": 199.90,
        "Calças": 159.90,
        "Camisas": 119.90,
        "Casacos": 219.90,
        "Saias e Vestidos": 149.90,
    }
    return precos_categoria.get(categoria, 99.90)


def image_url(sku, filename):
    if not sku or not filename:
        return ""
    path = IMAGE_DIR / sku / filename
    if not path.exists():
        return ""
    return f"{IMAGE_BASE_URL}/{sku}/{filename}"


def build_product(row):
    sku = row.get("SKU", "")
    nome = row.get("Nome do Produto", "")
    categoria = row.get("Categoria", "")
    descricao = row.get("Texto Alt (Acessibilidade)", "")
    corredor = corredor_from_categoria(categoria)
    return (
        int(row.get("ID", "0")),
        nome,
        categoria,
        tipo_from_nome(nome),
        cor_from_nome(nome),
        "",
        "Acervo TCC",
        preco_from_produto(nome, categoria),
        1,
        categoria,
        corredor,
        f"Expositor {corredor}",
        descricao,
        sku,
        image_url(sku, row.get("Foto 1 (Frente)", "")),
        image_url(sku, row.get("Foto 2 (Costas)", "")),
        image_url(sku, row.get("Foto 3 (Lateral)", "")),
        image_url(sku, row.get("Foto 4 (Detalhe)", "")),
        descricao,
    )


def create_database(products):
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE produtos (
            id INTEGER PRIMARY KEY,
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
            descricao TEXT,
            sku TEXT UNIQUE,
            imagem TEXT,
            imagem_2 TEXT,
            imagem_3 TEXT,
            imagem_4 TEXT,
            texto_alt TEXT
        )
        """
    )
    cursor.executemany(
        """
        INSERT INTO produtos (
            id, nome, categoria, tipo, cor, tamanho, marca, preco, estoque,
            setor, corredor, prateleira, descricao, sku, imagem, imagem_2,
            imagem_3, imagem_4, texto_alt
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        products,
    )
    conn.commit()
    conn.close()


def main():
    xlsx_path = Path(os.environ.get("CATALOGO_XLSX", DEFAULT_XLSX))
    products = [build_product(row) for row in rows_from_xlsx(xlsx_path)]
    create_database(products)
    print(f"Banco criado em {DB_PATH} com {len(products)} produtos.")


if __name__ == "__main__":
    main()
