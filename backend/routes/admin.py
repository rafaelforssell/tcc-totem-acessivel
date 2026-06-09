"""
Rotas administrativas para gerenciamento de estoque.
Protegidas por senha via header X-Admin-Key.
"""
import os

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

from services.db_service import execute, fetchall

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, "..", ".env"))

ADMIN_KEY = os.getenv("ADMIN_KEY", "totem-admin-2024")

router = APIRouter(prefix="/admin", tags=["Admin"])


def verificar_chave(x_admin_key: str | None):
    if x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Chave de administrador invalida.")


class AtualizarEstoqueBody(BaseModel):
    estoque: int


class AtualizarProdutoBody(BaseModel):
    preco: float
    estoque: int
    setor: str
    corredor: str
    prateleira: str
    descricao: str


class CriarProdutoBody(BaseModel):
    nome: str
    categoria: str
    tipo: str
    cor: str
    tamanho: str
    marca: str
    preco: float
    estoque: int = 1
    setor: str
    corredor: str
    prateleira: str
    descricao: str
    sku: str
    imagem: str | None = ""
    texto_alt: str | None = ""


@router.get("/produtos")
def listar_produtos_admin(x_admin_key: str | None = Header(default=None)):
    """Lista todos os produtos com campos usados no totem."""
    verificar_chave(x_admin_key)
    produtos = fetchall(
        """
        SELECT id, nome, categoria, cor, tamanho, preco, estoque, sku, setor, corredor, prateleira, descricao
        FROM produtos
        ORDER BY categoria, nome
        """
    )
    return {"produtos": produtos, "total": len(produtos)}


@router.patch("/produto/{produto_id}/estoque")
def atualizar_estoque(
    produto_id: int,
    body: AtualizarEstoqueBody,
    x_admin_key: str | None = Header(default=None),
):
    """Atualiza o estoque de um produto pelo ID."""
    verificar_chave(x_admin_key)

    if body.estoque < 0:
        raise HTTPException(status_code=400, detail="Estoque nao pode ser negativo.")

    linhas = execute(
        "UPDATE produtos SET estoque = ? WHERE id = ?",
        (body.estoque, produto_id),
    )
    if linhas == 0:
        raise HTTPException(status_code=404, detail=f"Produto {produto_id} nao encontrado.")

    return {
        "ok": True,
        "produto_id": produto_id,
        "novo_estoque": body.estoque,
        "mensagem": "Estoque atualizado com sucesso." if body.estoque > 0 else "Produto marcado como esgotado.",
    }


@router.patch("/produto/{produto_id}/zerar")
def zerar_estoque(produto_id: int, x_admin_key: str | None = Header(default=None)):
    """Atalho para zerar o estoque de um produto."""
    verificar_chave(x_admin_key)
    linhas = execute("UPDATE produtos SET estoque = 0 WHERE id = ?", (produto_id,))
    if linhas == 0:
        raise HTTPException(status_code=404, detail=f"Produto {produto_id} nao encontrado.")
    return {"ok": True, "produto_id": produto_id, "mensagem": "Produto marcado como esgotado."}


@router.put("/produto/{produto_id}")
def atualizar_produto(
    produto_id: int,
    body: AtualizarProdutoBody,
    x_admin_key: str | None = Header(default=None),
):
    """Atualiza os campos principais usados pelo totem em tempo real."""
    verificar_chave(x_admin_key)

    if body.estoque < 0:
        raise HTTPException(status_code=400, detail="Estoque nao pode ser negativo.")
    if body.preco < 0:
        raise HTTPException(status_code=400, detail="Preco nao pode ser negativo.")

    linhas = execute(
        """
        UPDATE produtos
        SET preco = ?, estoque = ?, setor = ?, corredor = ?, prateleira = ?, descricao = ?
        WHERE id = ?
        """,
        (
            body.preco,
            body.estoque,
            body.setor.strip(),
            body.corredor.strip(),
            body.prateleira.strip(),
            body.descricao.strip(),
            produto_id,
        ),
    )
    if linhas == 0:
        raise HTTPException(status_code=404, detail=f"Produto {produto_id} nao encontrado.")

    produto = fetchall(
        """
        SELECT id, nome, categoria, cor, tamanho, preco, estoque, sku, setor, corredor, prateleira, descricao
        FROM produtos
        WHERE id = ?
        """,
        (produto_id,),
    )
    return {
        "ok": True,
        "produto_id": produto_id,
        "produto": produto[0] if produto else None,
        "mensagem": "Produto updated com sucesso.",
    }


@router.post("/produto")
def criar_produto(
    body: CriarProdutoBody,
    x_admin_key: str | None = Header(default=None),
):
    """Cadastra um novo produto no estoque do totem."""
    verificar_chave(x_admin_key)

    if body.estoque < 0:
        raise HTTPException(status_code=400, detail="Estoque nao pode ser negativo.")
    if body.preco < 0:
        raise HTTPException(status_code=400, detail="Preco nao pode ser negativo.")

    sku_limpo = body.sku.strip()
    # Verifica se SKU já existe
    existente = fetchall("SELECT id FROM produtos WHERE sku = ?", (sku_limpo,))
    if existente:
        raise HTTPException(status_code=400, detail="Produto com este SKU ja cadastrado.")

    try:
        execute(
            """
            INSERT INTO produtos (
                nome, categoria, tipo, cor, tamanho, marca, preco, estoque,
                setor, corredor, prateleira, descricao, sku, imagem, texto_alt
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                body.nome.strip(),
                body.categoria.strip(),
                body.tipo.strip(),
                body.cor.strip(),
                body.tamanho.strip(),
                body.marca.strip(),
                body.preco,
                body.estoque,
                body.setor.strip(),
                body.corredor.strip(),
                body.prateleira.strip(),
                body.descricao.strip(),
                sku_limpo,
                body.imagem.strip() if body.imagem else "",
                body.texto_alt.strip() if body.texto_alt else "",
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao inserir no banco: {e}")

    # Retorna o produto recém cadastrado
    novo_produto = fetchall(
        """
        SELECT id, nome, categoria, cor, tamanho, preco, estoque, sku, setor, corredor, prateleira, descricao
        FROM produtos
        WHERE sku = ?
        """,
        (sku_limpo,),
    )

    return {
        "ok": True,
        "produto": novo_produto[0] if novo_produto else None,
        "mensagem": "Produto cadastrado com sucesso.",
    }
