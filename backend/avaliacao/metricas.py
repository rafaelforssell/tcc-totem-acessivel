"""Funcoes de metricas compartilhadas pelos scripts de avaliacao."""
import re
import unicodedata


def percentil(valores, p):
    """Percentil com interpolacao linear (mesmo criterio do numpy/Excel PERCENTIL.INC)."""
    if not valores:
        return None
    ordenados = sorted(valores)
    if len(ordenados) == 1:
        return ordenados[0]
    posicao = (len(ordenados) - 1) * p / 100
    base = int(posicao)
    fracao = posicao - base
    if base + 1 >= len(ordenados):
        return ordenados[base]
    return ordenados[base] + (ordenados[base + 1] - ordenados[base]) * fracao


def normalizar_para_wer(texto):
    """Minusculas, sem acentos e sem pontuacao: avalia as palavras, nao a formatacao."""
    texto = unicodedata.normalize("NFKD", (texto or "").lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"[^\w\s]", " ", texto)
    return " ".join(texto.split())


def distancia_palavras(referencia, hipotese):
    """Retorna (substituicoes + delecoes + insercoes, total de palavras da referencia)."""
    ref = referencia.split()
    hip = hipotese.split()
    anterior = list(range(len(hip) + 1))
    for i, palavra_ref in enumerate(ref, 1):
        atual = [i] + [0] * len(hip)
        for j, palavra_hip in enumerate(hip, 1):
            custo = 0 if palavra_ref == palavra_hip else 1
            atual[j] = min(anterior[j] + 1, atual[j - 1] + 1, anterior[j - 1] + custo)
        anterior = atual
    return anterior[-1], len(ref)
