import os
import httpx
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, "..", ".env")
load_dotenv(ENV_PATH)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

_local_whisper_model = None

def obter_whisper_local():
    global _local_whisper_model
    if _local_whisper_model is None:
        try:
            import whisper
            print("[STT] Carregando modelo local Whisper (tiny)...")
            _local_whisper_model = whisper.load_model("tiny")
            print("[STT] Modelo local Whisper carregado com sucesso.")
        except Exception as e:
            print(f"[STT] Erro ao carregar Whisper local: {e}")
            _local_whisper_model = False
    return _local_whisper_model


async def transcrever_audio(caminho_audio):
    # Se temos a chave do Groq, usamos o Groq (sub-segundo, na nuvem)
    if GROQ_API_KEY:
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
        except Exception as e:
            print("Erro na transcrição via Groq, tentando local...", e)

    # Fallback local com o pacote whisper
    model = obter_whisper_local()
    if model:
        try:
            print(f"[STT] Transcrevendo localmente: {caminho_audio}")
            import asyncio
            # Como a transcrição local do whisper bloqueia, rodamos no threadpool
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None, 
                lambda: model.transcribe(caminho_audio, language="pt", fp16=False)
            )
            texto = result.get("text", "").strip()
            print("Texto STT (Whisper Local):", texto)
            return texto
        except Exception as e:
            print(f"[STT] Erro na transcrição local: {e}")
            
    print("Erro: Nenhuma transcrição disponível (sem chave Groq e falha no Whisper local)")
    return ""