from services.pipeline_service import pipeline_processar

print("--- TESTE 1: Saudação e pergunta aleatória ---")
res1 = pipeline_processar("Olá, quem descobriu o Brasil?")
print("Res:", res1["resposta"])

print("\n--- TESTE 2: Nova busca ---")
res2 = pipeline_processar("Eu queria comprar uma camisa dry fit preta")
print("Res:", res2["resposta"])
if res2["resultados"]:
    print("Produto retornado:", res2["resultados"][0]["nome"])

print("\n--- TESTE 3: Pergunta de contexto ---")
res3 = pipeline_processar("Onde fica?")
print("Res:", res3["resposta"])

print("\n--- TESTE 4: Pergunta de contexto 2 ---")
res4 = pipeline_processar("E tem estoque disso?")
print("Res:", res4["resposta"])
