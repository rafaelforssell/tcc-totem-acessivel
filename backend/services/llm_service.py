import os
import httpx
import json
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, "..", ".env")
load_dotenv(ENV_PATH)

API_KEY = os.getenv("GROQ_API_KEY")


async def classificar_intencao(pergunta, idioma="pt"):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    prompt_sistema = """
Você é o classificador de intenções de um totem de loja de roupas.
Responda APENAS com JSON válido no formato:
{
  "intencao": "NOVA_BUSCA" ou "SOBRE_PRODUTO" ou "IR_PARA_MAPA" ou "OUTROS",
  "palavras_chave": ["palavra1", "palavra2"]
}

REGRAS:
- NOVA_BUSCA: Usuário busca produto novo ("quero uma camisa", "tem calça?", "quero saber sobre a calça jeans slim").
  Preencha palavras_chave com os termos do produto.
- SOBRE_PRODUTO: Usuário pergunta sobre produto JÁ mostrado usando pronomes ou referências diretas ("essa calça, qual a cor?").
- IR_PARA_MAPA: Usuário aceita a sugestão de ir até o produto ou pede para ver o mapa ("sim", "quero", "me mostre o caminho", "onde fica o corredor?").
- OUTROS: Saudações, despedidas, agradecimentos ou perguntas aleatórias.
"""

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": pergunta}
        ],
        "temperature": 0.0,
        "max_tokens": 100,
        "response_format": {"type": "json_object"}
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=20.0)
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            content = content.replace('```json', '').replace('```', '').strip()
            return json.loads(content)
    except Exception as e:
        print("Erro no classificar_intencao:", e)
        return {"intencao": "OUTROS", "palavras_chave": []}


async def perguntar_llm(pergunta, contexto_produtos=None, idioma="pt"):
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    if contexto_produtos:
        info_produtos = f"DADOS DO BANCO DE DADOS (use APENAS estes para responder):\n{contexto_produtos}"
    else:
        info_produtos = "Nenhum produto no contexto."

    lang_instruction = "Responda em Português do Brasil." if idioma == "pt" else "Responda em Inglês."

    prompt_sistema = f"""
Você é o assistente virtual de um totem de uma loja de roupas.

REGRAS OBRIGATÓRIAS:
1. {lang_instruction}
2. Responda em no máximo 3 frases curtas e diretas.
3. Ao falar de um produto, NUNCA informe o corredor, prateleira ou localização física. Guarde segredo sobre a localização.
4. Ao mostrar ou falar sobre um produto, OBRIGATORIAMENTE termine a frase perguntando se a pessoa quer saber onde fica. (Exemplo: "Posso te informar onde encontrar, você deseja?")
5. NUNCA invente preços, cores, locais ou nomes. Use APENAS as informações abaixo.
6. NUNCA use emojis, asteriscos ou formatação markdown. O texto será lido em voz alta.

{info_produtos}
"""

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": pergunta}
        ],
        "temperature": 0.0,
        "max_tokens": 150
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=20.0)
            data = response.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        print("Erro no perguntar_llm:", e)
        return "Desculpe, estou com problemas técnicos no momento."
