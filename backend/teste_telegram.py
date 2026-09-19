import asyncio
import os

import httpx
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()


async def test():
    if not BOT_TOKEN or not CHAT_ID:
        print("Defina TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID no backend/.env")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": "🤖 *Teste de Notificação do Totem Acessível* 🚀",
        "parse_mode": "Markdown"
    }

    print(f"Enviando mensagem para {CHAT_ID}...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10.0)
            print("Status Code:", response.status_code)
            print("Response:", response.text)
    except Exception as e:
        print("Erro no envio:", e)

if __name__ == "__main__":
    asyncio.run(test())
