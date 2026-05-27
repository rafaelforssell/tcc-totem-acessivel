"""
Rota para acionar chamada de atendente com notificação via Telegram.
"""
from fastapi import APIRouter
from pydantic import BaseModel

from services.telegram_service import enviar_alerta_atendente

router = APIRouter(tags=["Atendente"])


class ProdutoAtendenteBody(BaseModel):
    nome: str
    setor: str | None = None
    corredor: str | int | None = None


class ChamarAtendenteBody(BaseModel):
    foto_base64: str | None = None
    totem_id: str = "Totem 1"
    produtos: list[ProdutoAtendenteBody] = []


@router.post("/chamar-atendente")
async def chamar_atendente(body: ChamarAtendenteBody):
    """
    Recebe captura do mapa do frontend e envia alerta ao atendente via Telegram.
    """
    resultado = await enviar_alerta_atendente(
        foto_base64=body.foto_base64,
        totem_id=body.totem_id,
        produtos=body.produtos,
    )
    return {
        "ok": resultado.get("ok", False),
        "modo": resultado.get("modo", "nenhum"),
        "mensagem": "Atendente notificado com sucesso!" if resultado.get("ok") else "Falha ao notificar atendente.",
        "erro": resultado.get("erro"),
    }

