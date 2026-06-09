from fastapi.testclient import TestClient
from main import app
from routes import admin

client = TestClient(app)
ADMIN_KEY = admin.ADMIN_KEY


def test_excluir_produto_nao_encontrado():
    response = client.delete("/admin/produto/9999", headers={"X-Admin-Key": ADMIN_KEY})
    assert response.status_code == 404


def test_excluir_categoria_nao_encontrada():
    response = client.delete("/admin/categoria/CategoriaInexistente", headers={"X-Admin-Key": ADMIN_KEY})
    assert response.status_code == 404


def test_criar_e_excluir_categoria_sucesso():
    # 1. Cria nova categoria
    payload = {
        "categoria": "Sessao de Teste",
        "corredor": "11",
        "setor": "Teste"
    }
    response = client.post("/admin/categoria", json=payload, headers={"X-Admin-Key": ADMIN_KEY})
    assert response.status_code == 200
    assert response.json()["ok"] is True
    
    # 2. Exclui a categoria criada
    response_del = client.delete("/admin/categoria/Sessao de Teste", headers={"X-Admin-Key": ADMIN_KEY})
    assert response_del.status_code == 200
    assert response_del.json()["ok"] is True
