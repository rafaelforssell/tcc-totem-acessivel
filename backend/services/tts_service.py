import edge_tts
import uuid
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_AUDIO = os.path.join(BASE_DIR, "audios")

if not os.path.exists(PASTA_AUDIO):
    os.makedirs(PASTA_AUDIO)


async def falar(texto):
    texto = texto.replace("*", "")
    import re
    texto = re.sub(r'\bse[çc][aã]o\((?:ões|oês|oes)\)', 'seções', texto)
    texto = re.sub(r'\bsess[aã]o\((?:ões|oês|oes)\)', 'sessões', texto)
    texto = re.sub(r'\bop[çc][aã]o\((?:ões|oês|oes)\)', 'opções', texto)
    texto = re.sub(r'\(s\)', 's', texto)
    texto = texto.replace("(", "").replace(")", "")
    
    nome = f"{uuid.uuid4()}.mp3"
    caminho = os.path.join(PASTA_AUDIO, nome)

    communicate = edge_tts.Communicate(
        text=texto,
        voice="pt-BR-FranciscaNeural"
    )

    await communicate.save(caminho)

    return f"audios/{nome}"
