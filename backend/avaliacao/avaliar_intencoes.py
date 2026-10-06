"""
Bateria de testes do classificador de intencoes (Llama 3.3 via Groq).

Uso (dentro de backend/, com GROQ_API_KEY no .env):
    python avaliacao/avaliar_intencoes.py
    python avaliacao/avaliar_intencoes.py --frases avaliacao/frases_intencoes.csv --intervalo 2.5

Gera:
    - acuracia geral e por intencao (acertos / total de frases daquela intencao)
    - matriz de confusao
    - latencia p50 e p95 do classificador
    - quantas respostas vieram da IA e quantas do fallback por regras
    - avaliacao/resultados/intencoes_<data>.csv com cada frase
"""
import argparse
import asyncio
import csv
import os
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime

AVALIACAO_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AVALIACAO_DIR))

from services.llm_service import GROQ_API_KEY, classificar_intencao  # noqa: E402
from metricas import percentil  # noqa: E402

INTENCOES = ["NOVA_BUSCA", "SOBRE_PRODUTO", "IR_PARA_MAPA", "ENCERRAR", "OUTROS"]


def ler_frases(caminho):
    with open(caminho, encoding="utf-8") as f:
        return [(linha["frase"], linha["intencao_esperada"].strip()) for linha in csv.DictReader(f)]


async def executar(frases, intervalo):
    resultados = []
    for i, (frase, esperada) in enumerate(frases, 1):
        inicio = time.perf_counter()
        analise = await classificar_intencao(frase)
        latencia = time.perf_counter() - inicio
        obtida = analise.get("intencao", "OUTROS")
        fonte = analise.get("fonte", "?")
        marca = "ok  " if obtida == esperada else "ERRO"
        print(f"[{i:3}/{len(frases)}] {marca} {esperada:14} -> {obtida:14} ({fonte}, {latencia:.2f}s) {frase}")
        resultados.append({
            "frase": frase,
            "esperada": esperada,
            "obtida": obtida,
            "acertou": obtida == esperada,
            "fonte": fonte,
            "latencia_s": round(latencia, 4),
            "palavras_chave": " ".join(analise.get("palavras_chave", [])),
        })
        if intervalo:
            await asyncio.sleep(intervalo)
    return resultados


def relatorio(resultados, apenas_llm):
    base = [r for r in resultados if r["fonte"] == "llm"] if apenas_llm else resultados
    titulo = "SOMENTE RESPOSTAS DA IA" if apenas_llm else "TODAS AS RESPOSTAS"
    print(f"\n===== {titulo} ({len(base)} frases) =====")
    if not base:
        print("Nenhuma resposta nesta categoria.")
        return

    acertos = sum(r["acertou"] for r in base)
    print(f"Acuracia geral: {acertos}/{len(base)} = {acertos / len(base):.1%}")

    print("\nAcuracia por intencao:")
    por_intencao = defaultdict(list)
    for r in base:
        por_intencao[r["esperada"]].append(r["acertou"])
    for intencao in INTENCOES:
        valores = por_intencao.get(intencao, [])
        if valores:
            print(f"  {intencao:14} {sum(valores):3}/{len(valores):<3} = {sum(valores) / len(valores):.1%}")

    print("\nMatriz de confusao (linhas = esperada, colunas = obtida):")
    matriz = Counter((r["esperada"], r["obtida"]) for r in base)
    colunas = INTENCOES + sorted({r["obtida"] for r in base} - set(INTENCOES))
    print(" " * 15 + "".join(f"{c[:12]:>13}" for c in colunas))
    for esperada in INTENCOES:
        print(f"{esperada:15}" + "".join(f"{matriz[(esperada, c)]:>13}" for c in colunas))

    latencias = [r["latencia_s"] for r in base]
    print(f"\nLatencia do classificador: p50 = {percentil(latencias, 50):.3f}s | "
          f"p95 = {percentil(latencias, 95):.3f}s | media = {sum(latencias) / len(latencias):.3f}s")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--frases", default=os.path.join(AVALIACAO_DIR, "frases_intencoes.csv"))
    parser.add_argument("--intervalo", type=float, default=2.5,
                        help="segundos entre chamadas, para nao estourar o limite da Groq (padrao 2.5)")
    args = parser.parse_args()

    if not GROQ_API_KEY:
        print("AVISO: GROQ_API_KEY nao configurada. O resultado medira apenas o fallback por regras.")

    frases = ler_frases(args.frases)
    resultados = asyncio.run(executar(frases, args.intervalo))

    fontes = Counter(r["fonte"] for r in resultados)
    print(f"\nOrigem das respostas: {dict(fontes)}")
    relatorio(resultados, apenas_llm=False)
    if fontes.get("regras"):
        print("\nATENCAO: parte das respostas veio do fallback por regras (erro ou limite da API).")
        relatorio(resultados, apenas_llm=True)

    pasta = os.path.join(AVALIACAO_DIR, "resultados")
    os.makedirs(pasta, exist_ok=True)
    saida = os.path.join(pasta, f"intencoes_{datetime.now():%Y%m%d_%H%M%S}.csv")
    with open(saida, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(resultados[0]), delimiter=";")
        writer.writeheader()
        writer.writerows(resultados)
    print(f"\nDetalhes salvos em {saida}")


if __name__ == "__main__":
    main()
