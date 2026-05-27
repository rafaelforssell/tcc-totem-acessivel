"""
Serviço de notificações via Telegram.
Usado para alertar o atendente quando um cliente pede ajuda no totem.
"""
import os
import base64
import httpx
from datetime import datetime
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, "..", ".env")
load_dotenv(ENV_PATH)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


async def enviar_alerta_atendente(foto_base64: str | None = None, totem_id: str = "Totem 1") -> dict:
    """
    Envia um alerta no Telegram quando o cliente pede um atendente.
    
    Args:
        foto_base64: String base64 da imagem do mapa (opcional)
        totem_id: Identificador do totem (ex: "Totem 1")
    
    Returns:
        dict com status e mensagem
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[Telegram] Token ou Chat ID não configurados.")
        return {"ok": False, "erro": "Telegram não configurado"}

    agora = datetime.now().strftime("%H:%M:%S")
    # Escapa caracteres HTML para evitar quebras se totem_id contiver símbolos especiais
    totem_id_safe = str(totem_id).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    
    texto = (
        f"🔔 <b>Cliente precisando de ajuda!</b>\n\n"
        f"📍 <b>Local:</b> {totem_id_safe}\n"
        f"🕐 <b>Horário:</b> {agora}\n\n"
        f"Por favor, dirija-se ao totem para atender o cliente."
    )

    async with httpx.AsyncClient(timeout=15.0) as client:
        # Se tem foto do mapa, envia como foto com legenda
        if foto_base64 and str(foto_base64).strip() and str(foto_base64).lower() not in ("null", "none", "undefined"):
            try:
                # Remove prefixo data:image/...;base64, se presente
                if "," in foto_base64:
                    foto_base64 = foto_base64.split(",", 1)[1]

                foto_bytes = base64.b64decode(foto_base64)

                response = await client.post(
                    f"{TELEGRAM_API}/sendPhoto",
                    data={
                        "chat_id": TELEGRAM_CHAT_ID,
                        "caption": texto,
                        "parse_mode": "HTML",
                    },
                    files={"photo": ("mapa.png", foto_bytes, "image/png")},
                )
                response.raise_for_status()
                return {"ok": True, "modo": "foto"}
            except Exception as e:
                print(f"[Telegram] Erro ao enviar foto: {e}. Tentando só texto...")

        # Fallback: só texto
        try:
            response = await client.post(
                f"{TELEGRAM_API}/sendMessage",
                json={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "text": texto,
                    "parse_mode": "HTML",
                },
            )
            response.raise_for_status()
            return {"ok": True, "modo": "texto"}
        except Exception as e:
            print(f"[Telegram] Erro ao enviar mensagem: {e}")
            return {"ok": False, "erro": str(e)}

