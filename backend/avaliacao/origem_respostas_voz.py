"""
Classifica a origem de cada resposta da avaliacao de voz: regra do pipeline, LLM ou fallback.

O cliente so recebe a resposta final, entao a origem e inferida em duas etapas:
1. a transcricao e reprocessada no pipeline local, com o LLM simulado, para contar
   quantas chamadas ao modelo aquela frase exige (zero = resolvida por regra do pipeline);
2. nas frases que exigem o modelo, o tempo da etapa de IA medido no servidor separa
   chamadas reais (>= 0,2 s) de fallback apos erro da API (quase instantaneo).

Uso (dentro de backend/):
    python avaliacao/origem_respostas_voz.py avaliacao/resultados/voz_<data>.csv
"""
import asyncio
import csv
import sys
from collections import Counter

sys.path.insert(0, ".")
sys.path.insert(0, "avaliacao")
from services import pipeline_service  # noqa: E402

esperadas = {l["frase"]: l["intencao_esperada"] for l in csv.DictReader(open("avaliacao/frases_intencoes.csv", encoding="utf-8"))}
ENTRADA = sys.argv[1]
linhas = list(csv.DictReader(open(ENTRADA, encoding="utf-8-sig"), delimiter=";"))

chamadas = Counter()
# Regras do pipeline levam milissegundos; uma chamada real ao modelo, algumas centenas
LIMIAR_LLM_S = 0.2


async def fake_classificar(pergunta, idioma="pt"):
    chamadas["classificar"] += 1
    return {"intencao": fake_classificar.intencao, "palavras_chave": [], "fonte": "llm"}


async def fake_perguntar(*a, **k):
    chamadas["responder"] += 1
    return "resposta"


pipeline_service.classificar_intencao = fake_classificar
pipeline_service.perguntar_llm = fake_perguntar

resultado = []
for l in linhas:
    chamadas.clear()
    fake_classificar.intencao = esperadas.get(l["referencia"], "OUTROS")
    pipeline_service.limpar_memoria(f"origem-{l['arquivo']}")
    asyncio.run(pipeline_service.pipeline_processar(l["transcricao"], "pt", sessao_id=f"origem-{l['arquivo']}"))
    usa_llm = chamadas["classificar"] + chamadas["responder"] > 0
    ia = float(l["ia_s"])
    if not usa_llm:
        origem = "regra_do_pipeline"
    elif ia >= LIMIAR_LLM_S:
        origem = "llm"
    else:
        origem = "fallback_provavel"
    resultado.append((l["arquivo"], origem, ia, chamadas["classificar"], chamadas["responder"], l["referencia"]))

print(Counter(r[1] for r in resultado))
for r in resultado:
    if r[1] != "llm":
        print(r)

with open(ENTRADA.replace(".csv", "_origem.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["arquivo", "origem", "ia_s", "chamadas_classificacao", "chamadas_resposta", "referencia"])
    w.writerows(resultado)
