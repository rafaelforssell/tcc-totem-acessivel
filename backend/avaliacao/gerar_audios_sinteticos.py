"""
Gera as frases do roteiro (audios/referencias.csv) com vozes sinteticas do Edge-TTS,
para avaliar STT e latencia quando nao ha gravacoes de pessoas reais.

Usa vozes diferentes da voz do totem (pt-BR-FranciscaNeural). Audio sintetico e
mais limpo que a fala real, entao o WER obtido tende a ser otimista: declarar no texto.

Uso (dentro de backend/):
    python avaliacao/gerar_audios_sinteticos.py
    python avaliacao/avaliar_voz.py --audios avaliacao/audios_sinteticos --url https://totem-acessivel.onrender.com
"""
import asyncio
import csv
import os

import edge_tts

AVALIACAO_DIR = os.path.dirname(os.path.abspath(__file__))
VOZES = {"antonio": "pt-BR-AntonioNeural", "thalita": "pt-BR-ThalitaMultilingualNeural"}


async def main():
    origem = os.path.join(AVALIACAO_DIR, "audios", "referencias.csv")
    destino = os.path.join(AVALIACAO_DIR, "audios_sinteticos")
    os.makedirs(destino, exist_ok=True)

    with open(origem, encoding="utf-8") as f:
        frases = [linha["texto_referencia"] for linha in csv.DictReader(f)]

    linhas = []
    for apelido, voz in VOZES.items():
        for i, frase in enumerate(frases, 1):
            nome = f"{apelido}_frase{i:02}.mp3"
            await edge_tts.Communicate(text=frase, voice=voz).save(os.path.join(destino, nome))
            linhas.append((nome, frase))
            print(f"{nome}: {frase}")

    with open(os.path.join(destino, "referencias.csv"), "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["arquivo", "texto_referencia"])
        writer.writerows(linhas)
    print(f"\n{len(linhas)} audios gerados em {destino}")


if __name__ == "__main__":
    asyncio.run(main())
