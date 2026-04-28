from services.llm_service import perguntar_llm

print("Iniciando teste...")

resposta = perguntar_llm("Onde fica o arroz?")

print("RESPOSTA:")
print(resposta)