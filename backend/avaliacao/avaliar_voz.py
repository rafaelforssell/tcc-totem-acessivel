"""
Avaliacao de voz ponta a ponta: WER da transcricao e latencia p50/p95.

Envia cada audio gravado para o endpoint /query-audio do backend (local ou Render),
exatamente como o totem faz, e compara a transcricao com o texto de referencia.

Preparacao:
    1. Grave os audios (de preferencia pessoas reais, no microfone do totem) em
       avaliacao/audios/ (webm, wav, mp3, m4a ou ogg).
    2. Preencha avaliacao/audios/referencias.csv com as colunas:
           arquivo,texto_referencia
       (o texto exatamente como foi falado).

Uso (dentro de backend/, com o servidor rodando):
    python avaliacao/avaliar_voz.py
    python avaliacao/avaliar_voz.py --url https://totem-acessivel.onrender.com --intervalo 3

Gera:
    - WER geral (soma dos erros / soma das palavras de referencia) e WER medio por frase
    - latencia p50 e p95 ponta a ponta (medida no cliente) e por etapa (STT, IA, TTS)
    - avaliacao/resultados/voz_<data>.csv com cada audio
"""
import argparse
import csv
import mimetypes
import os
import sys
import time
import uuid
from datetime import datetime

import requests

AVALIACAO_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AVALIACAO_DIR)

from metricas import distancia_palavras, normalizar_para_wer, percentil  # noqa: E402


CAMPOS = [
    "arquivo", "referencia", "transcricao", "erros_palavras", "palavras_referencia", "wer",
    "latencia_cliente_s", "stt_s", "ia_s", "tts_s", "total_servidor_s", "acao", "resposta",
]


def ler_referencias(pasta):
    caminho = os.path.join(pasta, "referencias.csv")
    with open(caminho, encoding="utf-8") as f:
        return [(linha["arquivo"].strip(), linha["texto_referencia"].strip()) for linha in csv.DictReader(f)]


def enviar_audio(url, caminho, sessao_id):
    # Comeca cada frase sem contexto de conversa anterior
    requests.post(f"{url.rstrip('/')}/reset", headers={"X-Session-Id": sessao_id}, timeout=60)
    tipo = mimetypes.guess_type(caminho)[0] or "audio/webm"
    with open(caminho, "rb") as f:
        inicio = time.perf_counter()
        resposta = requests.post(
            f"{url.rstrip('/')}/query-audio",
            files={"audio": (os.path.basename(caminho), f, tipo)},
            data={"idioma": "pt"},
            headers={"X-Session-Id": sessao_id},
            timeout=120,
        )
        latencia = time.perf_counter() - inicio
    resposta.raise_for_status()
    return resposta.json(), latencia


def resumo_latencia(nome, valores):
    valores = [v for v in valores if v is not None]
    if not valores:
        return
    print(f"  {nome:22} p50 = {percentil(valores, 50):6.3f}s | p95 = {percentil(valores, 95):6.3f}s | "
          f"media = {sum(valores) / len(valores):6.3f}s")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--audios", default=os.path.join(AVALIACAO_DIR, "audios"))
    parser.add_argument("--intervalo", type=float, default=3.0,
                        help="segundos entre envios, para nao estourar o limite da Groq (padrao 3)")
    args = parser.parse_args()

    referencias = ler_referencias(args.audios)
    resultados = []
    erros_total = palavras_total = 0

    # O CSV e gravado a cada audio, para nao perder resultados se a execucao for interrompida
    pasta = os.path.join(AVALIACAO_DIR, "resultados")
    os.makedirs(pasta, exist_ok=True)
    saida = os.path.join(pasta, f"voz_{datetime.now():%Y%m%d_%H%M%S}.csv")
    arquivo_csv = open(saida, "w", newline="", encoding="utf-8-sig")
    writer = csv.DictWriter(arquivo_csv, fieldnames=CAMPOS, delimiter=";")
    writer.writeheader()

    for i, (arquivo, referencia) in enumerate(referencias, 1):
        caminho = os.path.join(args.audios, arquivo)
        if not os.path.exists(caminho):
            print(f"[{i:3}/{len(referencias)}] PULADO: {arquivo} ainda nao foi gravado")
            continue
        # Sessao nova por audio: cada frase e avaliada sem contexto de conversa anterior
        dados, latencia = enviar_audio(args.url, caminho, f"avaliacao-{uuid.uuid4().hex[:12]}")
        transcricao = dados.get("transcricao", "")
        erros, palavras = distancia_palavras(normalizar_para_wer(referencia), normalizar_para_wer(transcricao))
        erros_total += erros
        palavras_total += palavras
        wer = erros / palavras if palavras else 0.0
        tempos = dados.get("tempos", {})
        print(f"[{i:3}/{len(referencias)}] WER {wer:6.1%} | {latencia:5.2f}s | {arquivo}\n"
              f"        ref: {referencia}\n        stt: {transcricao}")
        resultados.append({
            "arquivo": arquivo,
            "referencia": referencia,
            "transcricao": transcricao,
            "erros_palavras": erros,
            "palavras_referencia": palavras,
            "wer": round(wer, 4),
            "latencia_cliente_s": round(latencia, 3),
            "stt_s": tempos.get("stt_s"),
            "ia_s": tempos.get("ia_s"),
            "tts_s": tempos.get("tts_s"),
            "total_servidor_s": tempos.get("total_s"),
            "acao": dados.get("acao"),
            "resposta": dados.get("resposta"),
        })
        writer.writerow(resultados[-1])
        arquivo_csv.flush()
        if args.intervalo and i < len(referencias):
            time.sleep(args.intervalo)

    arquivo_csv.close()
    if not resultados:
        os.remove(saida)
        print("\nNenhum audio encontrado. Grave os arquivos listados em referencias.csv.")
        return

    print(f"\n===== RESULTADO ({len(resultados)} audios) =====")
    if palavras_total:
        print(f"WER geral: {erros_total}/{palavras_total} palavras = {erros_total / palavras_total:.2%}")
        print(f"WER medio por frase: {sum(r['wer'] for r in resultados) / len(resultados):.2%}")
    print("\nLatencia:")
    resumo_latencia("ponta a ponta (cliente)", [r["latencia_cliente_s"] for r in resultados])
    resumo_latencia("total no servidor", [r["total_servidor_s"] for r in resultados])
    resumo_latencia("STT", [r["stt_s"] for r in resultados])
    resumo_latencia("IA (pipeline + LLM)", [r["ia_s"] for r in resultados])
    resumo_latencia("TTS", [r["tts_s"] for r in resultados])

    print(f"\nDetalhes salvos em {saida}")


if __name__ == "__main__":
    main()
