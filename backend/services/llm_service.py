import os
import httpx
import json
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, "..", ".env")
load_dotenv(ENV_PATH)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


def obter_config_llm():
    """Define a URL, headers e modelo conforme as chaves disponíveis."""
    if GROQ_API_KEY:
        return {
            "url": "https://api.groq.com/openai/v1/chat/completions",
            "headers": {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            "model": "llama-3.3-70b-versatile"
        }
    elif OPENROUTER_API_KEY:
        return {
            "url": "https://openrouter.ai/api/v1/chat/completions",
            "headers": {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/yeagerdavo/tcc-totem-acessivel",
                "X-Title": "Totem Acessivel"
            },
            "model": "google/gemini-2.5-flash"
        }
    return None


async def classificar_intencao(pergunta, idioma="pt"):
    config = obter_config_llm()
    if not config:
        return {"intencao": "OUTROS", "palavras_chave": []}

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
- IR_PARA_MAPA: também quando pedir "ver tudo que falamos no mapa", "mostrar todos no mapa", "mapa de tudo", "ver os lugares".
- NOVA_BUSCA: Usuário busca um produto ("quero uma camisa", "tem calça?"). NÃO classifique a palavra "mapa" como busca de produto.
- NOVA_BUSCA: se o usuário disser "short" ou "shorts", use a palavra-chave "bermuda".
- SOBRE_PRODUTO: Usuário pergunta detalhes (preço, cor, tamanho) de um produto. Se a pergunta for sobre a LOCALIZAÇÃO ("onde fica?"), classifique como IR_PARA_MAPA e não SOBRE_PRODUTO.
- OUTROS: Saudações, agradecimentos, perguntas sobre pagamento, boleto, pix, cartão, parcelamento, horário ou temas fora de produto/localização.
"""

    payload = {
        "model": config["model"],
        "messages": [
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": pergunta}
        ],
        "temperature": 0.0,
        "max_tokens": 100
    }
    
    if "groq" in config["url"]:
        payload["response_format"] = {"type": "json_object"}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(config["url"], headers=config["headers"], json=payload, timeout=20.0)
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            content = content.replace('```json', '').replace('```', '').strip()
            return json.loads(content)
    except Exception as e:
        print("Erro no classificar_intencao:", e)
        # Fallback local baseado em regras simples se a API falhar ou der Rate Limit (429)
        texto = pergunta.lower()
        
        # Se for encerramento
        if any(term in texto for term in ["tchau", "obrigado", "obrigada", "valeu", "encerrar", "ate logo"]):
            return {"intencao": "ENCERRAR", "palavras_chave": []}
            
        # Se for pedido de mapa ou localização
        if any(term in texto for term in ["mapa", "onde fica", "onde e", "caminho", "corredor", "localizacao"]):
            return {"intencao": "IR_PARA_MAPA", "palavras_chave": []}
            
        # Extrai palavras e remove stopwords para busca
        stopwords = {
            "eu", "quero", "queria", "saber", "mais", "sobre", "tem", "voce", "roupa", "roupas",
            "qual", "quais", "uma", "um", "de", "da", "do", "comprar", "buscar", "procurar"
        }
        palavras_pergunta = [w.strip(".,?!") for w in texto.split()]
        palavras_chave = [w for w in palavras_pergunta if len(w) > 2 and w not in stopwords]
        
        if palavras_chave:
            # Mapeamento simples de sinônimo "short" -> "bermuda" para o banco
            palavras_final = ["bermuda" if p in ["short", "shorts"] else p for p in palavras_chave]
            return {"intencao": "NOVA_BUSCA", "palavras_chave": palavras_final}
            
        return {"intencao": "OUTROS", "palavras_chave": []}



async def perguntar_llm(pergunta, contexto_produtos=None, idioma="pt", historico=None, todos_produtos=None):
    config = obter_config_llm()
    if not config:
        return "Desculpe, a chave da IA nao esta configurada no momento."

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
2. Responda em no máximo 3 frases curtas, diretas e naturais, como uma pessoa atendendo na loja.
3. EXTREMAMENTE IMPORTANTE: NUNCA diga em qual corredor, prateleira, andar ou setor o produto está. Guarde segredo absoluto sobre a localização física.
4. Quando o usuário demonstrar interesse ou gostar de um produto (responder positivamente, confirmar, dizer "sim", "perfeito", "gostei", etc.), ofereça de forma natural mostrar onde o produto fica, usando o mapa. Ex: "Que ótimo! Quer que eu te mostre onde encontrar?", "Posso te mostrar no mapa onde fica, se quiser." Faça isso de forma leve, como um atendente real faria.
5. Ao apresentar um produto pela primeira vez, forneça todos os detalhes dele (descrição, preço, cores e tamanhos disponíveis). Termine sempre com uma pergunta de interesse natural (ex: "Gostou das opções?", "O que achou?", "Tem alguma dúvida sobre ele?").
6. NUNCA invente preços, cores, locais ou nomes. Use APENAS as informações do banco de dados fornecidas abaixo.
7. NUNCA use emojis, asteriscos ou formatação markdown. O texto será lido em voz alta.
8. Se a pergunta tiver erro, gíria ou frase incompleta, interprete pela intenção mais provável usando o contexto da conversa e os dados do banco.
9. Se o assunto for pagamento, boleto, Pix ou cartão, diga de forma breve que essa confirmação deve ser feita no caixa e volte a oferecer ajuda com produtos.

{info_produtos}
{info_todos_produtos}
"""

    messages = [{"role": "system", "content": prompt_sistema}]
    
    if historico:
        for msg in historico[-10:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
            
    messages.append({"role": "user", "content": pergunta})

    payload = {
        "model": config["model"],
        "messages": messages,
        "temperature": 0.0,
        "max_tokens": 150
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(config["url"], headers=config["headers"], json=payload, timeout=20.0)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        print("Erro no perguntar_llm:", e)
        # Fallback local conversacional amigável se a API do Groq falhar ou der Rate Limit (429)
        try:
            if todos_produtos:
                p = todos_produtos[-1] # Pega o último produto adicionado/mencionado
                nome = p.get("nome", "produto")
                preco = p.get("preco", 0.0)
                cor = p.get("cor", "")
                
                if idioma == "pt":
                    res = f"Encontrei o {nome} por R$ {preco:.2f}. "
                    if cor:
                        res += f"Temos ele na cor {cor}. "
                    res += "Gostou dessa opção? Quer que eu te mostre o caminho no mapa?"
                    return res
                else:
                    res = f"I found the {nome} for ${preco:.2f}. "
                    if cor:
                        res += f"We have it in {cor}. "
                    res += "Did you like this option? Would you like me to show you the route on the map?"
                    return res
        except Exception as fallback_err:
            print("Erro ao gerar fallback de produto:", fallback_err)

        if idioma == "pt":
            return "Perfeito! Consegui encontrar as opções no nosso sistema. Gostaria de ver a localização no mapa?"
        else:
            return "Perfect! I found the options in our system. Would you like to see the location on the map?"

