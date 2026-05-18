import edge_tts
import uuid
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_AUDIO = os.path.join(BASE_DIR, "audios")

if not os.path.exists(PASTA_AUDIO):
    os.makedirs(PASTA_AUDIO)


async def falar(texto):
    texto = texto.replace("*", "")
    nome = f"{uuid.uuid4()}.mp3"
    caminho = os.path.join(PASTA_AUDIO, nome)

    communicate = edge_tts.Communicate(
        text=texto,
        voice="pt-BR-FranciscaNeural"
    )

    await communicate.save(caminho)

    return f"audios/{nome}"
