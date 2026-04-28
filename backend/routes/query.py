from fastapi import APIRouter, UploadFile, File
from services.pipeline_service import pipeline_processar
from services.stt_service import transcrever_audio
from services.tts_service import falar
import os
import time

router = APIRouter()


@router.get("/query-text")
async def query_text(q: str):
    return await pipeline_processar(q)


@router.post("/query-audio")
async def query_audio(audio: UploadFile = File(...)):

    inicio_total = time.time()

    caminho = f"temp_{audio.filename}"

    with open(caminho, "wb") as f:
        f.write(await audio.read())

    print("Áudio recebido")

    # STT
    inicio_stt = time.time()
    texto = await transcrever_audio(caminho)
    fim_stt = time.time()

    print("STT concluído:", round(fim_stt - inicio_stt, 2), "seg")
    
    if not texto:
        # Se não ouviu nada ou deu erro, encerra rápido
        if os.path.exists(caminho):
            os.remove(caminho)
        return {
            "transcricao": "Não entendi.",
            "resposta": "Desculpe, não consegui ouvir direito. Pode repetir?",
            "resultados": [],
            "audio": ""
        }

    # IA / Pipeline
    inicio_ia = time.time()
    resultado = await pipeline_processar(texto)
    fim_ia = time.time()

    print("IA concluída:", round(fim_ia - inicio_ia, 2), "seg")

    resposta_texto = resultado["resposta"]

    # TTS
    inicio_tts = time.time()
    arquivo_audio = await falar(resposta_texto)
    fim_tts = time.time()

    print("TTS concluído:", round(fim_tts - inicio_tts, 2), "seg")

    # Remove arquivo temporário enviado
    if os.path.exists(caminho):
        os.remove(caminho)

    fim_total = time.time()

    print("TOTAL:", round(fim_total - inicio_total, 2), "seg")

    return {
        "transcricao": texto,
        "resposta": resposta_texto,
        "resultados": resultado["resultados"],
        "audio": arquivo_audio
    }