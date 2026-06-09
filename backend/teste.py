import asyncio
import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

print("--- ENV VARS LOADED FROM .env ---")
print("DATABASE_URL:", os.getenv("DATABASE_URL"))
print("GROQ_API_KEY:", os.getenv("GROQ_API_KEY"))
print("TELEGRAM_BOT_TOKEN:", os.getenv("TELEGRAM_BOT_TOKEN"))
print("TELEGRAM_CHAT_ID:", os.getenv("TELEGRAM_CHAT_ID"))

# Test db_service
from services import db_service
print("\n--- DB SERVICE TEST ---")
print("usando_postgres():", db_service.usando_postgres())
try:
    prods = db_service.fetchall("SELECT COUNT(*) FROM produtos")
    print("Fetchall success, count:", prods)
except Exception as e:
    print("Fetchall failed:", e)

# Test LLM
from services.llm_service import perguntar_llm, classificar_intencao
async def test_llm():
    print("\n--- LLM TEST ---")
    try:
        res = await perguntar_llm("Olá, tudo bem?")
        print("perguntar_llm response:", res)
    except Exception as e:
        print("perguntar_llm failed:", e)
        
    try:
        res_class = await classificar_intencao("Quero uma camiseta azul")
        print("classificar_intencao response:", res_class)
    except Exception as e:
        print("classificar_intencao failed:", e)

if __name__ == "__main__":
    asyncio.run(test_llm())