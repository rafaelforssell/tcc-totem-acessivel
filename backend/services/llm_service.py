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
  "intencao": "NOVA_BUSCA" ou "SOBRE_PRODUTO" ou "IR_PARA_MAPA" ou "ENCERRAR" ou "OUTROS",
  "palavras_chave": ["palavra1", "palavra2"]
}

REGRAS:
- ENCERRAR: Usuário está se despedindo, agradecendo e recusando mais ajuda ("tchau", "obrigado", "valeu", "encerrar", "até logo", "não, obrigado", "valeu, tchau").
- IR_PARA_MAPA: Usuário pede para ver o MAPA, ou pergunta ONDE o produto fica/está ("onde é?", "onde fica?", "onde é que é", "eu quero mapa", "me mostre o caminho", "qual o corredor?").
- NOVA_BUSCA: Usuário busca um produto ("quero uma camisa", "tem calça?"). NÃO classifique a palavra "mapa" como busca de produto.
- SOBRE_PRODUTO: Usuário pergunta detalhes (preço, cor, tamanho) de um produto. Se a pergunta for sobre a LOCALIZAÇÃO ("onde fica?"), classifique como IR_PARA_MAPA e não SOBRE_PRODUTO.
- OUTROS: Saudações, agradecimentos, etc.
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
3. EXTREMAMENTE IMPORTANTE: NUNCA diga em qual corredor, prateleira, andar ou setor o produto está. Guarde segredo absoluto sobre a localização física.
4. Se o usuário perguntar onde está, NUNCA responda a localização. Apenas diga: "Quer saber aonde está?" ou "Posso te mostrar no mapa, você deseja?".
5. Ao mostrar ou falar sobre um produto pela primeira vez, OBRIGATORIAMENTE termine a frase perguntando: "Quer saber aonde está?" ou "Posso te informar onde encontrar, você deseja?".
6. NUNCA invente preços, cores, locais ou nomes. Use APENAS as informações do banco de dados fornecidas abaixo.
7. NUNCA use emojis, asteriscos ou formatação markdown. O texto será lido em voz alta.

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
