"""
Rota para acionar chamada de atendente com notificação via Telegram.
"""
from fastapi import APIRouter
from pydantic import BaseModel

from services.telegram_service import enviar_alerta_atendente

router = APIRouter(tags=["Atendente"])


class ChamarAtendenteBody(BaseModel):
    foto_base64: str | None = None
    totem_id: str = "Totem 1"


@router.post("/chamar-atendente")
async def chamar_atendente(body: ChamarAtendenteBody):
    """
    Recebe captura do mapa do frontend e envia alerta ao atendente via Telegram.
    """
    resultado = await enviar_alerta_atendente(
        foto_base64=body.foto_base64,
        totem_id=body.totem_id,
    )
    return {
        "ok": resultado.get("ok", False),
        "modo": resultado.get("modo", "nenhum"),
        "mensagem": "Atendente notificado com sucesso!" if resultado.get("ok") else "Falha ao notificar atendente.",
    }
