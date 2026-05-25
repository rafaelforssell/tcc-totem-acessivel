import os
import httpx
import json
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, "..", ".env")
load_dotenv(ENV_PATH)

API_KEY = os.getenv("GROQ_API_KEY")


async def classificar_intencao(pergunta, idioma="pt"):
    if not API_KEY:
        return {"intencao": "OUTROS", "palavras_chave": []}

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

REGRAS OBRIGATÓRIAS PARA palavras_chave:
- Extraia apenas as palavras-chave essenciais do produto (substantivos, adjetivos de cor/tipo/marca) no SINGULAR.
- NUNCA inclua números ou quantidades (como "dois", "duas", "3").
- NUNCA inclua verbos gerais em formato infinitivo/conjugado (como "treinar", "correr"). Em vez disso, converta para o substantivo/adjetivo correspondente que possa estar no banco de dados (ex: "treino", "corrida").
- Exemplo: "duas camisas para treinar" -> {"intencao": "NOVA_BUSCA", "palavras_chave": ["camisa", "treino"]}
- Exemplo: "calças azuis" -> {"intencao": "NOVA_BUSCA", "palavras_chave": ["calca", "azul"]}

REGRAS DE INTENÇÃO:
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
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            content = content.replace('```json', '').replace('```', '').strip()
            return json.loads(content)
    except Exception as e:
        print("Erro no classificar_intencao:", e)
        return {"intencao": "OUTROS", "palavras_chave": []}


async def perguntar_llm(pergunta, contexto_produtos=None, idioma="pt", historico=None, todos_produtos=None):
    if not API_KEY:
        return "Desculpe, a chave da IA nao esta configurada no momento."

    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    if contexto_produtos:
        info_produtos = f"DADOS DO BANCO DE DADOS (use APENAS estes para responder):\n{contexto_produtos}"
    else:
        info_produtos = "Nenhum produto no contexto."

    info_todos_produtos = ""
    if todos_produtos:
        linhas_todos = []
        for p in todos_produtos:
            linhas_todos.append(f"- {p['nome']} (R$ {p['preco']:.2f})")
        info_todos_produtos = "\nPRODUTOS JÁ CONVERSADOS/MENCIONADOS NESSA SESSÃO:\n" + "\n".join(linhas_todos)

    lang_instruction = "Responda em Português do Brasil." if idioma == "pt" else "Responda em Inglês."

    prompt_sistema = f"""
Você é o assistente virtual de um totem de uma loja de roupas.

REGRAS OBRIGATÓRIAS:
1. {lang_instruction}
2. Responda em no máximo 3 frases curtas e diretas.
3. EXTREMAMENTE IMPORTANTE: NUNCA diga em qual corredor, prateleira, andar ou setor o produto está. Guarde segredo absoluto sobre a localização física.
4. Se o usuário perguntar onde está ou confirmar que gostou do produto e quer ver a localização, responda de forma prestativa confirmando que vai mostrar no mapa (ex: "Claro, vou te mostrar no mapa!" ou "Excelente, veja a localização no mapa!").
5. Ao apresentar um produto pela primeira vez, forneça todos os detalhes dele (descrição, preço, cores e tamanhos disponíveis) e OBRIGATORIAMENTE termine a frase perguntando se o usuário gostou das opções apresentadas (ex: "Gostou das opções?", "O que achou deste produto?"). NUNCA pergunte se ele quer ver no mapa ou onde está na primeira frase, espere que ele demonstre interesse ou responda positivamente antes.
6. NUNCA invente preços, cores, locais ou nomes. Use APENAS as informações do banco de dados fornecidas abaixo.
7. NUNCA use emojis, asteriscos ou formatação markdown. O texto será lido em voz alta.

{info_produtos}
{info_todos_produtos}
"""

    messages = [{"role": "system", "content": prompt_sistema}]
    
    if historico:
        # Pega as últimas 10 interações para manter o contexto curto e otimizado
        for msg in historico[-10:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
            
    messages.append({"role": "user", "content": pergunta})

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.0,
        "max_tokens": 150
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=20.0)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        print("Erro no perguntar_llm:", e)
        return "Desculpe, estou com problemas técnicos no momento."
