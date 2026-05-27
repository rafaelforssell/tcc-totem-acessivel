import asyncio
import httpx

BOT_TOKEN = "8974271580:AAEonkpmPhCvayhiI96jG26F1CKZW5gL8ZE"
CHAT_ID = "8917844351"

async def test():
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
