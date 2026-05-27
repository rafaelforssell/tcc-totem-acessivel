"""
Servico de notificacoes via Telegram para alertar o atendente do totem.
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
        return f"Telegram retornou HTTP {response.status_code}: {details}"
    return str(exc)


token_configured, chat_id_configured = _get_telegram_config()
print(f"[Telegram] Token configurado: {'SIM' if token_configured else 'NAO'}")
print(f"[Telegram] Chat ID configurado: {'SIM' if chat_id_configured else 'NAO'}")


async def enviar_alerta_atendente(
    foto_base64: str | None = None,
    totem_id: str = "Totem 1",
    produtos: list | None = None,
) -> dict:
    """
    Envia um alerta no Telegram quando um cliente pede um atendente.
    """
    telegram_bot_token, telegram_chat_id = _get_telegram_config()
    if not telegram_bot_token or not telegram_chat_id:
        print("[Telegram] Token ou Chat ID nao configurados.")
        return {"ok": False, "erro": "Telegram nao configurado"}

    telegram_api = _build_telegram_api(telegram_bot_token)
    now_text = datetime.now().strftime("%H:%M:%S")
    totem_id_safe = str(totem_id).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    produtos = produtos or []

    linhas_produtos = []
    for produto in produtos[:6]:
        if hasattr(produto, "model_dump"):
            produto = produto.model_dump()
        nome = str(produto.get("nome", "")).strip() if isinstance(produto, dict) else ""
        setor = str(produto.get("setor", "")).strip() if isinstance(produto, dict) else ""
        corredor = str(produto.get("corredor", "")).strip() if isinstance(produto, dict) else ""
        if not nome:
            continue
        detalhes = []
        if setor:
            detalhes.append(setor)
        if corredor:
            detalhes.append(f"corredor {corredor}")
        linha = f"- {nome}"
        if detalhes:
            linha += f" ({', '.join(detalhes)})"
        linhas_produtos.append(linha.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

    bloco_produtos = ""
    if linhas_produtos:
        bloco_produtos = "\n<b>Produtos de interesse:</b>\n" + "\n".join(linhas_produtos)

    texto = (
        "<b>Cliente precisando de ajuda</b>\n\n"
        f"<b>Local:</b> {totem_id_safe}\n"
        f"<b>Horario:</b> {now_text}\n"
        "<b>Mapa:</b> foto em anexo"
        f"{bloco_produtos}"
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
                    "[Telegram] Erro ao enviar foto: "
                    f"{_format_telegram_error(exc)}. Tentando enviar so texto..."
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
            print(f"[Telegram] Erro ao enviar mensagem: {erro_formatado}")
            return {"ok": False, "erro": erro_formatado}
