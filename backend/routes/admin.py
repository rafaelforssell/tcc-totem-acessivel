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
        "mensagem": "Produto atualizado com sucesso.",
    }
