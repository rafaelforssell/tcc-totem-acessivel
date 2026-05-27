import asyncio
import httpx

async def test():
    url = "https://totem-acessivel.onrender.com/chamar-atendente"
    payload = {
        "foto_base64": None,
        "totem_id": "Totem 1 (Teste Remoto)"
    }
    
    print("Chamando endpoint do Render /chamar-atendente...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=15.0)
            print("Status Code:", response.status_code)
            print("Response:", response.text)
    except Exception as e:
        print("Erro na chamada:", e)

if __name__ == "__main__":
    asyncio.run(test())
