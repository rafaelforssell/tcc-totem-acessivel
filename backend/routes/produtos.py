from fastapi import APIRouter
from services.produtos_service import listar_produtos_db, buscar_produto_db

router = APIRouter()

@router.get("/produtos")
def listar_produtos():
    return listar_produtos_db()

@router.get("/buscar-produto")
def buscar_produto(nome: str):
    return buscar_produto_db(nome)