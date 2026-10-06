import edge_tts
import uuid
import os
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_AUDIO = os.path.join(BASE_DIR, "audios")

# Os audios so precisam existir ate o totem tocar a resposta
AUDIO_RETENCAO_SEGUNDOS = int(os.getenv("AUDIO_RETENCAO_SEGUNDOS", "600"))

if not os.path.exists(PASTA_AUDIO):
    os.makedirs(PASTA_AUDIO)


def limpar_audios_antigos():
    """Apaga audios (respostas e entradas esquecidas) mais velhos que a retencao."""
    limite = time.time() - AUDIO_RETENCAO_SEGUNDOS
    for nome in os.listdir(PASTA_AUDIO):
        if not nome.endswith((".mp3", ".wav", ".webm", ".ogg", ".m4a")):
            continue
        caminho = os.path.join(PASTA_AUDIO, nome)
        try:
            if os.path.getmtime(caminho) < limite:
                os.remove(caminho)
        except OSError:
            pass


async def falar(texto):
    texto = texto.replace("*", "")
    import re
    texto = re.sub(r'\bse[çc][aã]o\((?:ões|oês|oes)\)', 'seções', texto)
    texto = re.sub(r'\bsess[aã]o\((?:ões|oês|oes)\)', 'sessões', texto)
    texto = re.sub(r'\bop[çc][aã]o\((?:ões|oês|oes)\)', 'opções', texto)
    texto = re.sub(r'\(s\)', 's', texto)
    texto = texto.replace("(", "").replace(")", "")
    
    limpar_audios_antigos()

    nome = f"{uuid.uuid4()}.mp3"
    caminho = os.path.join(PASTA_AUDIO, nome)

    communicate = edge_tts.Communicate(
        text=texto,
        voice="pt-BR-FranciscaNeural"
    )

    await communicate.save(caminho)

    return f"audios/{nome}"
