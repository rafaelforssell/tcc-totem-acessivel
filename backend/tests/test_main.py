from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_health_ok():
    resposta = client.get("/health")

    assert resposta.status_code == 200
    payload = resposta.json()
    assert payload["status"] == "ok"
    assert payload["db"] == "ok"
    assert payload["produtos"] >= 1


def test_produtos_endpoint_usa_schema_completo():
    resposta = client.get("/produtos")

    assert resposta.status_code == 200
    produto = resposta.json()["produtos"][0]
    assert "corredor" in produto
    assert "prateleira" in produto
