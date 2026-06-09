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
    nome: str
    categoria: str
    tipo: str
    cor: str
    tamanho: str
    marca: str
    preco: float
    estoque: int
    setor: str
    corredor: str
    prateleira: str
    descricao: str
    sku: str
    imagem: str | None = ""
    texto_alt: str | None = ""


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
        SELECT id, nome, categoria, tipo, cor, tamanho, marca, preco, estoque, sku, setor, corredor, prateleira, descricao, imagem, texto_alt
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
    """Atualiza todos os campos de um produto em tempo real."""
    verificar_chave(x_admin_key)

    if body.estoque < 0:
        raise HTTPException(status_code=400, detail="Estoque nao pode ser negativo.")
    if body.preco < 0:
        raise HTTPException(status_code=400, detail="Preco nao pode ser negativo.")

    sku_limpo = body.sku.strip()
    # Verifica se o novo SKU já existe em outro produto
    existente = fetchall("SELECT id FROM produtos WHERE sku = ? AND id != ?", (sku_limpo, produto_id))
    if existente:
        raise HTTPException(status_code=400, detail="Outro produto com este SKU ja esta cadastrado.")

    imagem_val = body.imagem.strip() if body.imagem else ""
    if imagem_val.lower() in ("opcional", "optional"):
        imagem_val = ""

    linhas = execute(
        """
        UPDATE produtos
        SET nome = ?, categoria = ?, tipo = ?, cor = ?, tamanho = ?, marca = ?,
            preco = ?, estoque = ?, setor = ?, corredor = ?, prateleira = ?,
            descricao = ?, sku = ?, imagem = ?, texto_alt = ?
        WHERE id = ?
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
            imagem_val,
            body.texto_alt.strip() if body.texto_alt else "",
            produto_id,
        ),
    )
    if linhas == 0:
        raise HTTPException(status_code=404, detail=f"Produto {produto_id} nao encontrado.")

    produto = fetchall(
        """
        SELECT id, nome, categoria, tipo, cor, tamanho, marca, preco, estoque, sku, setor, corredor, prateleira, descricao, imagem, texto_alt
        FROM produtos
        WHERE id = ?
        """,
        (produto_id,),
    )
    return {
        "ok": True,
        "produto_id": produto_id,
        "produto": produto[0] if produto else None,
        "mensagem": "Produto updated successfully.",
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

    imagem_val = body.imagem.strip() if body.imagem else ""
    if imagem_val.lower() in ("opcional", "optional"):
        imagem_val = ""

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
                imagem_val,
                body.texto_alt.strip() if body.texto_alt else "",
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao inserir no banco: {e}")

    # Retorna o produto recém cadastrado
    novo_produto = fetchall(
        """
        SELECT id, nome, categoria, tipo, cor, tamanho, marca, preco, estoque, sku, setor, corredor, prateleira, descricao, imagem, texto_alt
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


@router.delete("/produto/{produto_id}")
def excluir_produto(produto_id: int, x_admin_key: str | None = Header(default=None)):
    """Exclui um produto pelo ID."""
    verificar_chave(x_admin_key)
    linhas = execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
    if linhas == 0:
        raise HTTPException(status_code=404, detail=f"Produto {produto_id} nao encontrado.")
    return {"ok": True, "mensagem": "Produto excluido com sucesso."}


@router.delete("/categoria/{categoria}")
def excluir_categoria(categoria: str, x_admin_key: str | None = Header(default=None)):
    """Exclui todos os produtos de uma categoria (excluindo a sessao)."""
    verificar_chave(x_admin_key)
    cat_nome = categoria.strip()
    linhas = execute("DELETE FROM produtos WHERE categoria = ?", (cat_nome,))
    if linhas == 0:
        raise HTTPException(status_code=404, detail=f"Nenhum produto encontrado na categoria '{cat_nome}'.")
    return {"ok": True, "mensagem": f"Categoria '{cat_nome}' excluida com sucesso."}


class CriarCategoriaBody(BaseModel):
    categoria: str
    corredor: str
    setor: str


@router.post("/categoria")
def criar_categoria(
    body: CriarCategoriaBody,
    x_admin_key: str | None = Header(default=None),
):
    """Cria uma nova sessao/categoria no totem inserindo um item inicial (placeholder com estoque 0)."""
    verificar_chave(x_admin_key)
    cat_nome = body.categoria.strip()
    if not cat_nome:
        raise HTTPException(status_code=400, detail="Nome da categoria nao pode ser vazio.")

    # Verifica se a categoria já existe
    existente = fetchall("SELECT id FROM produtos WHERE categoria = ?", (cat_nome,))
    if existente:
        raise HTTPException(status_code=400, detail="Esta categoria/sessao ja existe.")

    sku = f"placeholder_{cat_nome.lower().replace(' ', '_')}"
    # Garante que o SKU seja único
    sku_orig = sku
    i = 1
    while fetchall("SELECT id FROM produtos WHERE sku = ?", (sku,)):
        sku = f"{sku_orig}_{i}"
        i += 1

    execute(
        """
        INSERT INTO produtos (
            nome, categoria, tipo, cor, tamanho, marca, preco, estoque,
            setor, corredor, prateleira, descricao, sku, imagem, texto_alt
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f"Item Inicial {cat_nome}",
            cat_nome,
            cat_nome,
            "",
            "",
            "",
            0.0,
            0, # estoque = 0 (placeholder)
            body.setor.strip(),
            body.corredor.strip(),
            "",
            f"Item inicial para a categoria {cat_nome}.",
            sku,
            "",
            "",
        ),
    )
    return {"ok": True, "mensagem": f"Sessao '{cat_nome}' criada com sucesso."}
