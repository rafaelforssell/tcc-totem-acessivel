import os
import httpx
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, "..", ".env")
load_dotenv(ENV_PATH)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

async def transcrever_audio(caminho_audio):
    if not GROQ_API_KEY:
        print("Erro: GROQ_API_KEY não configurada no .env")
        return ""

    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }

    try:
        async with httpx.AsyncClient() as client:
            with open(caminho_audio, "rb") as f:
                # O Groq suporta webm diretamente, não precisamos de ffmpeg!
                files = {"file": (os.path.basename(caminho_audio), f, "audio/webm")}
                data = {
                    "model": "whisper-large-v3-turbo",
                    "language": "pt"
                }

                response = await client.post(url, headers=headers, data=data, files=files, timeout=30.0)

                if response.status_code == 200:
                    texto = response.json().get("text", "").strip()
                    print("Texto STT (Groq):", texto)
                    return texto
                else:
                    print(f"Erro Groq API ({response.status_code}):", response.text)
                    return ""
    except Exception as e:
        print("Erro na transcrição via Groq:", e)
        return ""