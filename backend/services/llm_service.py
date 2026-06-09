import os
import httpx
import json
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, "..", ".env")
load_dotenv(ENV_PATH)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def obter_config_llm():
    """Define a URL, headers e modelo conforme a chave da Groq disponível."""
    if GROQ_API_KEY:
        return {
            "url": "https://api.groq.com/openai/v1/chat/completions",
            "headers": {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            "model": "llama-3.3-70b-versatile"
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
- NUNCA confunda verbos de movimento/ação (como "sair", "ir", "saia daí") com a vestimenta física "saia" (skirt). Não extraia "saia" como palavra-chave a menos que o usuário esteja se referindo explicitamente à peça de roupa saia.
- NUNCA inclua palavras de pessoa/relacionamento como "namorada", "namorado", "esposa", "marido", "mãe", "pai", "filho", "amiga", "amigo", "prima", "tia" ou pronomes possessivos. Extraia APENAS o produto em si.
- NUNCA inclua palavras de ocasião, feriados, comemorações ou propósitos gerais (como "aniversario", "festa", "casamento", "trabalho", "academia", "presente", "noite"). Extraia apenas o produto físico em si.
- Se o usuário estiver fazendo uma afirmação de agrado ou gosto sobre um produto anterior (ex: "gostei do vestido", "achei massa a calça") mas em seguida perguntar sobre outro produto (ex: "você tem cinto?", "tem camiseta?"), NÃO extraia a palavra-chave do produto anterior (ex: "vestido", "calça"). Extraia APENAS o produto novo que está sendo ativamente buscado (ex: "cinto", "camiseta").
- Exemplo: "vestido pra minha namorada" -> {"intencao": "NOVA_BUSCA", "palavras_chave": ["vestido"]}
- Exemplo: "duas camisas para treinar" -> {"intencao": "NOVA_BUSCA", "palavras_chave": ["camisa", "treino"]}
- Exemplo: "calças azuis" -> {"intencao": "NOVA_BUSCA", "palavras_chave": ["calca", "azul"]}
- Exemplo: "Gostei do vestido. Você tem cinto?" -> {"intencao": "NOVA_BUSCA", "palavras_chave": ["cinto"]}

REGRAS DE INTENÇÃO:
- ENCERRAR: Usuário está se despedindo, agradecendo e recusando mais ajuda ("tchau", "obrigado", "valeu", "encerrar", "até logo", "não, obrigado", "valeu, tchau").
- IR_PARA_MAPA: Usuário pede para ver o MAPA, ou pergunta ONDE o produto fica/está ("onde é?", "onde fica?", "onde é que é", "eu quero mapa", "me mostre o caminho", "qual o corredor?").
- IR_PARA_MAPA: também quando pedir "ver tudo que falamos no mapa", "mostrar todos no mapa", "mapa de tudo", "ver os lugares".
- NOVA_BUSCA: Usuário busca um produto ("quero uma camisa", "tem calça?"). NÃO classifique a palavra "mapa" como busca de produto.
- NOVA_BUSCA: se o usuário disser "short" ou "shorts", use a palavra-chave "bermuda".
- SOBRE_PRODUTO: Usuário pergunta detalhes (preço, cor, tamanho) de um produto, ou questiona sobre as opções de tamanhos disponíveis (ex: "você tem que tamanho?", "tem tamanho M?", "gostei, você tem meu tamanho?"). Se a pergunta for sobre a LOCALIZAÇÃO ("onde fica?"), classifique como IR_PARA_MAPA e não SOBRE_PRODUTO.
- OUTROS: Saudações, agradecimentos, perguntas sobre pagamento, boleto, pix, cartão, parcelamento, horário ou temas fora de produto/localização.
"""

    payload = {
        "model": config["model"],
        "messages": [
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": pergunta}
        ],
        "temperature": 0.0,
        "max_tokens": 512
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
        TAMANHOS_CONHECIDOS = {
            "p", "m", "g", "gg", "pp", "xg", "xxg", "unico",
            "34", "36", "38", "40", "42", "44", "46", "48", "50",
            "35", "37", "39", "41", "43", "45"
        }
        stopwords = {
            "eu", "quero", "queria", "saber", "mais", "sobre", "tem", "voce", "roupa", "roupas",
            "qual", "quais", "uma", "um", "de", "da", "do", "comprar", "buscar", "procurar"
        }
        palavras_pergunta = [w.strip(".,?!") for w in texto.split()]
        palavras_chave = [w for w in palavras_pergunta if (len(w) > 2 or w in TAMANHOS_CONHECIDOS) and w not in stopwords]
        
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
4. NUNCA empurre o mapa por conta própria. Só fale de mapa ou localização se o usuário pedir explicitamente.
5. NUNCA peça para adicionar à lista de compras por conta própria. Ao apresentar opções, termine com uma pergunta natural e curta, como "Gostou de alguma delas?" ou "Quer ver outras opções?".
6. Se o pedido exato não existir, avise isso primeiro de forma gentil e só depois sugira algo parecido, deixando claro que é uma alternativa.
7. Ao apresentar um produto pela primeira vez, forneça os detalhes mais úteis dele (descrição, preço, cor e tamanho quando existirem). Termine com uma pergunta natural de continuidade.
8. NUNCA invente preços, cores, locais ou nomes. Use APENAS as informações do banco de dados fornecidas abaixo.
9. NUNCA use emojis, asteriscos ou formatação markdown. O texto será lido em voz alta.
10. Se a pergunta tiver erro, gíria ou frase incompleta, interprete pela intenção mais provável usando o contexto da conversa e os dados do banco.
11. Se o assunto for pagamento, boleto, Pix ou cartão, diga de forma breve que essa confirmação deve ser feita no caixa e volte a oferecer ajuda com produtos.

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
        "max_tokens": 1000
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(config["url"], headers=config["headers"], json=payload, timeout=20.0)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        print("Erro no perguntar_llm:", e)
        # Fallback local conversacional inteligente
        texto = pergunta.lower()
        
        # 1. Se for conversa casual, dúvida geral ou saudação
        if (contexto_produtos and "Conversa casual" in contexto_produtos) or any(w in texto for w in ["ola", "oi", "bom dia", "boa tarde", "boa noite"]):
            if "boa noite" in texto:
                return "Boa noite! Seja bem-vindo à nossa loja. Como posso ajudar você hoje?"
            elif "boa tarde" in texto:
                return "Boa tarde! Seja bem-vindo à nossa loja. Como posso ajudar você hoje?"
            elif "bom dia" in texto:
                return "Bom dia! Seja bem-vindo à nossa loja. Como posso ajudar você hoje?"
            else:
                return "Olá! Seja bem-vindo à nossa loja. Como posso ajudar você hoje?"

        # 2. Se for encerramento/agradecimento
        if any(w in texto for w in ["tchau", "obrigado", "obrigada", "valeu", "encerrar", "obrigado pelo seu tempo"]):
            return "De nada! Se precisar de mais alguma ajuda, estarei por aqui. Tenha um ótimo dia!"

        # 3. Se for busca de produtos com resultados reais
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
                    res += "O que achou?"
                    return res
                else:
                    res = f"I found the {nome} for ${preco:.2f}. "
                    if cor:
                        res += f"We have it in {cor}. "
                    res += "What do you think?"
                    return res
        except Exception as fallback_err:
            print("Erro ao gerar fallback de produto:", fallback_err)

        # 4. Caso genérico simples
        if idioma == "pt":
            return "Como posso ajudar você hoje?"
        else:
            return "How can I help you today?"


