from fastapi import APIRouter, UploadFile, File, Form, Header
from services.pipeline_service import pipeline_processar
from services.stt_service import transcrever_audio
from services.tts_service import falar
import os
import time
import uuid

router = APIRouter()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO_DIR = os.path.join(BASE_DIR, "audios")
os.makedirs(AUDIO_DIR, exist_ok=True)


@router.get("/query-text")
async def query_text(q: str, idioma: str = "pt", x_session_id: str | None = Header(default=None)):
    return await pipeline_processar(q, idioma, sessao_id=x_session_id)


@router.get("/welcome-audio")
async def welcome_audio(idioma: str = "pt"):
    resposta_texto = (
        "Bem-vindo ao Kiosk. O que deseja para hoje?"
        if idioma == "pt"
        else "Welcome to Kiosk. What would you like today?"
    )
    arquivo_audio = await falar(resposta_texto)
    return {
        "resposta": resposta_texto,
        "audio": arquivo_audio
    }


@router.post("/query-audio")
async def query_audio(
    audio: UploadFile = File(...),
    idioma: str = Form("pt"),
    x_session_id: str | None = Header(default=None),
):

    inicio_total = time.time()

    extensao = os.path.splitext(audio.filename or "audio.webm")[1] or ".webm"
    caminho = os.path.join(AUDIO_DIR, f"entrada_{uuid.uuid4()}{extensao}")

    with open(caminho, "wb") as f:
        f.write(await audio.read())

    print("Áudio recebido")

    try:

        # STT
        inicio_stt = time.time()
        texto = await transcrever_audio(caminho)
        fim_stt = time.time()

        print("STT concluído:", round(fim_stt - inicio_stt, 2), "seg")

        if texto is None:
            texto = ""

        # IA / Pipeline
        inicio_ia = time.time()
        resultado = await pipeline_processar(texto, idioma, sessao_id=x_session_id)
        fim_ia = time.time()

        print("IA concluída:", round(fim_ia - inicio_ia, 2), "seg")

        resposta_texto = resultado["resposta"]

        # TTS
        inicio_tts = time.time()
        arquivo_audio = await falar(resposta_texto)
        fim_tts = time.time()

        print("TTS concluído:", round(fim_tts - inicio_tts, 2), "seg")
    finally:
        # O audio do usuario e apagado sempre, inclusive quando STT/IA/TTS falham
        if os.path.exists(caminho):
            os.remove(caminho)

    fim_total = time.time()

    print("TOTAL:", round(fim_total - inicio_total, 2), "seg")

    return {
        "transcricao": texto,
        "resposta": resposta_texto,
        "resultados": resultado.get("resultados", []),
        "acao": resultado.get("acao", "NENHUM"),
        "auto_add_lista": resultado.get("auto_add_lista", False),
        "audio": arquivo_audio,
        "tempos": {
            "stt_s": round(fim_stt - inicio_stt, 3),
            "ia_s": round(fim_ia - inicio_ia, 3),
            "tts_s": round(fim_tts - inicio_tts, 3),
            "total_s": round(fim_total - inicio_total, 3),
        },
    }
