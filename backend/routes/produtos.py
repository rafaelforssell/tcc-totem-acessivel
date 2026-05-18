from fastapi import APIRouter
from services.produtos_service import listar_produtos_db, buscar_produto_db

router = APIRouter()

@router.get("/produtos")
def listar_produtos():
    """Lista todos os produtos cadastrados no catalogo."""
    return listar_produtos_db()

@router.get("/buscar-produto")
def buscar_produto(nome: str):
    """Busca produtos por nome, categoria, tipo, cor, marca ou descricao."""
    return buscar_produto_db(nome)
