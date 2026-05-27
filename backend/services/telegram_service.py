"""
Telegram notification service used to alert an attendant from the kiosk.
"""
import base64
import os
from datetime import datetime

import httpx
from dotenv import load_dotenv


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, "..", ".env")
load_dotenv(ENV_PATH)


def _get_telegram_config() -> tuple[str, str]:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    return token, chat_id


def _build_telegram_api(token: str) -> str:
    return f"https://api.telegram.org/bot{token}"


def _format_telegram_error(exc: Exception) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        response = exc.response
        try:
            details = response.json()
        except Exception:
            details = response.text
        return f"Telegram returned HTTP {response.status_code}: {details}"
    return str(exc)


token_configured, chat_id_configured = _get_telegram_config()
print(f"[Telegram] Token configured: {'YES' if token_configured else 'NO'}")
print(f"[Telegram] Chat ID configured: {'YES' if chat_id_configured else 'NO'}")


async def enviar_alerta_atendente(
    foto_base64: str | None = None,
    totem_id: str = "Totem 1",
) -> dict:
    """
    Sends a Telegram alert when a client asks for an attendant.
    """
    telegram_bot_token, telegram_chat_id = _get_telegram_config()
    if not telegram_bot_token or not telegram_chat_id:
        print("[Telegram] Token or Chat ID not configured.")
        return {"ok": False, "erro": "Telegram not configured"}

    telegram_api = _build_telegram_api(telegram_bot_token)
    now_text = datetime.now().strftime("%H:%M:%S")
    totem_id_safe = str(totem_id).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    texto = (
        "<b>Client needs help!</b>\n\n"
        f"<b>Location:</b> {totem_id_safe}\n"
        f"<b>Time:</b> {now_text}\n\n"
        "Please go to the kiosk to assist the client."
    )

    async with httpx.AsyncClient(timeout=15.0) as client:
        if (
            foto_base64
            and str(foto_base64).strip()
            and str(foto_base64).lower() not in ("null", "none", "undefined")
        ):
            try:
                if "," in foto_base64:
                    foto_base64 = foto_base64.split(",", 1)[1]

                foto_bytes = base64.b64decode(foto_base64, validate=True)
                response = await client.post(
                    f"{telegram_api}/sendPhoto",
                    data={
                        "chat_id": telegram_chat_id,
                        "caption": texto,
                        "parse_mode": "HTML",
                    },
                    files={"photo": ("mapa.png", foto_bytes, "image/png")},
                )
                response.raise_for_status()
                return {"ok": True, "modo": "foto"}
            except Exception as exc:
                print(
                    "[Telegram] Error sending photo: "
                    f"{_format_telegram_error(exc)}. Falling back to text..."
                )

        try:
            response = await client.post(
                f"{telegram_api}/sendMessage",
                data={
                    "chat_id": telegram_chat_id,
                    "text": texto,
                    "parse_mode": "HTML",
                },
            )
            response.raise_for_status()
            return {"ok": True, "modo": "texto"}
        except Exception as exc:
            erro_formatado = _format_telegram_error(exc)
            print(f"[Telegram] Error sending message: {erro_formatado}")
            return {"ok": False, "erro": erro_formatado}
