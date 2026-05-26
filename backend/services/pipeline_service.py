import os
import sqlite3
import unicodedata

from services.llm_service import classificar_intencao, perguntar_llm


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "..", "database", "produtos.db")

memoria = {
    "ultimos_produtos": [],
    "assunto_ativo": None,
    "historico_conversas": [],
    "produtos_mencionados": {},
}


def limpar_memoria():
    memoria["ultimos_produtos"] = []
    memoria["assunto_ativo"] = None
    memoria["historico_conversas"] = []
    memoria["produtos_mencionados"] = {}


def conectar_bd():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def normalizar_texto(texto):
    return (
        texto.lower()
        .replace("á", "a")
        .replace("ã", "a")
        .replace("â", "a")
        .replace("é", "e")
        .replace("ê", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ô", "o")
        .replace("ú", "u")
        .replace("ç", "c")
    )


def normalizar_texto(texto):
    sem_acento = unicodedata.normalize("NFKD", texto or "")
    return "".join(ch for ch in sem_acento if not unicodedata.combining(ch)).lower()


def obter_campo(produto, campo, indice=None, padrao=""):
    try:
        return produto[campo]
    except (IndexError, KeyError):
        if indice is None:
            return padrao
        return produto[indice] if len(produto) > indice else padrao


def formatar_produto(produto):
    return {
        "id": obter_campo(produto, "id", 0),
        "sku": obter_campo(produto, "sku"),
        "nome": obter_campo(produto, "nome", 1),
        "categoria": obter_campo(produto, "categoria", 2),
        "tipo": obter_campo(produto, "tipo", 3),
        "cor": obter_campo(produto, "cor", 4),
        "tamanho": obter_campo(produto, "tamanho", 5),
        "marca": obter_campo(produto, "marca", 6),
        "preco": obter_campo(produto, "preco", 7, 0),
        "estoque": obter_campo(produto, "estoque", 8, 0),
        "setor": obter_campo(produto, "setor", 9),
        "corredor": obter_campo(produto, "corredor", 10),
        "prateleira": obter_campo(produto, "prateleira", 11),
        "descricao": obter_campo(produto, "descricao", 12),
        "imagem": obter_campo(produto, "imagem"),
        "texto_alt": obter_campo(produto, "texto_alt"),
    }


def formatar_produto_para_contexto(p):
    return (
        f"Nome: {p['nome']} | Preco: R${p['preco']:.2f} | "
        f"Estoque: {p['estoque']} | Descricao: {p['descricao']} | "
        f"Cor: {p['cor']} | Tamanho: {p['tamanho']} | Marca: {p['marca']}"
    )


def texto_produto(produto):
    return normalizar_texto(
        " ".join(
            str(obter_campo(produto, campo))
            for campo in ["nome", "categoria", "tipo", "cor", "marca", "descricao", "sku", "setor"]
        ).replace("_", " ")
    )


def token_match(texto, token):
    token = normalizar_texto(token).strip()
    if not token:
        return False
    variantes = {token}
    if len(token) > 3 and token.endswith("s"):
        variantes.add(token[:-1])
    return any(variante in texto for variante in variantes)


def detectar_genero(tokens):
    texto = " ".join(normalizar_texto(token) for token in tokens)
    if any(palavra in texto for palavra in ["feminino", "feminina", "femininos", "femininas", "fem"]):
        return "fem"
    if any(palavra in texto for palavra in ["masculino", "masculina", "masculinos", "masculinas", "masc", "mas"]):
        return "mas"
    return None


def genero_produto(produto):
    texto = texto_produto(produto)
    sku = normalizar_texto(obter_campo(produto, "sku")).replace("_", " ")
    if any(palavra in texto or palavra in sku for palavra in ["feminino", "feminina", " fem"]):
        return "fem"
    if any(palavra in texto or palavra in sku for palavra in ["masculino", "masculina", " masc", " mas"]):
        return "mas"
    return None


def limpar_tokens_busca(palavras_chave):
    stopwords = {
        "eu", "quero", "queria", "saber", "mais", "sobre", "a", "o", "as", "os",
        "de", "da", "do", "tem", "ha", "me", "fale", "uma", "um", "por", "favor",
        "voce", "voces", "disponivel", "disponiveis",
    }
    return [
        normalizar_texto(palavra.strip(".,?!"))
        for palavra in palavras_chave
        if len(palavra.strip(".,?!")) > 2 and normalizar_texto(palavra.strip(".,?!")) not in stopwords
    ]


def buscar_produtos_sql(palavras_chave):
    if not palavras_chave:
        return []

    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM produtos ORDER BY nome, cor, tamanho")
    todos_produtos = cursor.fetchall()
    conn.close()

    tokens = limpar_tokens_busca(palavras_chave)
    genero = detectar_genero(tokens)
    tokens_sem_genero = [
        token for token in tokens
        if token not in {"feminino", "feminina", "femininos", "femininas", "fem", "masculino", "masculina", "masculinos", "masculinas", "masc", "mas"}
    ]

    def produto_valido(produto, exigir_todos=True):
        texto = texto_produto(produto)
        if genero and genero_produto(produto) != genero:
            return False
        if not tokens_sem_genero:
            return True
        if exigir_todos:
            return all(token_match(texto, token) for token in tokens_sem_genero)
        return any(token_match(texto, token) for token in tokens_sem_genero)

    produtos = [p for p in todos_produtos if produto_valido(p, exigir_todos=True)]
    if not produtos:
        produtos = [p for p in todos_produtos if produto_valido(p, exigir_todos=False)]

    return [formatar_produto(p) for p in produtos]


def is_encerramento(texto_baixo):
    palavras = texto_baixo.split()
    despedidas = {"tchau", "obrigado", "obrigada", "valeu", "encerrar", "bye", "thanks", "falou"}
    return (any(w in palavras for w in despedidas) or "ate logo" in normalizar_texto(texto_baixo)) and len(palavras) <= 4


def is_pedido_mapa(texto_baixo):
    texto = normalizar_texto(texto_baixo).replace(",", "").replace(".", "").replace("?", "").strip()
    afirmacoes = {
        "sim",
        "sim por favor",
        "por favor",
        "pode",
        "pode sim",
        "quero",
        "quero sim",
        "claro",
        "mostra",
        "mostre",
        "mostrar",
        "me mostra",
    }
    return (
        texto in afirmacoes
        or "mapa" in texto
        or "onde" in texto
        or "caminho" in texto
        or "corredor" in texto
        or "localizacao" in texto
    )


def is_pedido_resumo_rotas(texto_baixo):
    texto = normalizar_texto(texto_baixo)
    tem_rota = any(palavra in texto for palavra in ["rota", "rotas", "mapa", "lugares", "secoes", "sessao", "resumo"])
    tem_total = any(palavra in texto for palavra in ["todos", "todas", "geral", "resumo", "final"])
    return tem_rota and tem_total


def produtos_por_secao(produtos):
    secoes = {}
    for produto in produtos:
        corredor = produto.get("corredor")
        if not corredor or corredor in secoes:
            continue
        secoes[corredor] = produto
    return [secoes[chave] for chave in sorted(secoes, key=lambda valor: int(valor) if str(valor).isdigit() else 99)]


def selecionar_produtos_para_mapa(texto_baixo, produtos_memoria):
    pool = list(memoria.get("produtos_mencionados", {}).values()) or list(produtos_memoria)
    if not pool:
        return []

    stopwords_mapa = {
        "eu", "quero", "queria", "mostra", "mostrar", "mostre", "caminho", "mapa", "pra",
        "para", "mim", "por", "favor", "do", "da", "de", "o", "a", "os", "as", "no", "na",
        "elas", "eles", "ele", "ela", "gostei", "sim",
    }
    tokens = [
        token for token in normalizar_texto(texto_baixo).replace(",", " ").replace("?", " ").split()
        if len(token) > 2 and token not in stopwords_mapa
    ]
    if not tokens:
        return list(produtos_memoria[:1] if produtos_memoria else pool[:1])

    pontuados = []
    for produto in pool:
        texto = texto_produto(produto)
        score = sum(1 for token in tokens if token_match(texto, token))
        if score:
            pontuados.append((score, produto))

    if not pontuados:
        return list(produtos_memoria[:1] if produtos_memoria else pool[:1])

    maior_score = max(score for score, _ in pontuados)
    return [produto for score, produto in pontuados if score == maior_score or score >= 1]


def extrair_palavras_busca(texto_baixo):
    stopwords = {
        "eu", "quero", "queria", "saber", "mais", "sobre", "a", "o", "as", "os",
        "de", "da", "do", "tem", "ha", "me", "fale", "uma", "um", "por", "favor",
    }
    return [
        normalizar_texto(w.strip(".,?!"))
        for w in texto_baixo.split()
        if len(w.strip(".,?!")) > 2 and normalizar_texto(w.strip(".,?!")) not in stopwords
    ]


async def responder_sobre_produtos(pergunta, produtos, idioma):
    contexto = "Mantenha o assunto nestes produtos ja apresentados:\n" + "\n---\n".join(
        [formatar_produto_para_contexto(p) for p in produtos]
    )
    todos_prods = list(memoria["produtos_mencionados"].values())
    resposta = await perguntar_llm(
        pergunta,
        contexto_produtos=contexto,
        idioma=idioma,
        historico=memoria["historico_conversas"][:-1],
        todos_produtos=todos_prods
    )
    memoria["historico_conversas"].append({"role": "assistant", "content": resposta})
    return {"resposta": resposta, "resultados": produtos, "acao": "MOSTRAR_PRODUTOS"}



async def pipeline_processar(pergunta, idioma="pt"):
    print(f"\n--- Nova Requisicao: {pergunta} --- Idioma: {idioma}")
    texto_baixo = pergunta.lower()
    
    # Garante a inicialização do histórico e adiciona a pergunta do usuário
    if "historico_conversas" not in memoria:
        memoria["historico_conversas"] = []
    if "produtos_mencionados" not in memoria:
        memoria["produtos_mencionados"] = {}
        
    memoria["historico_conversas"].append({"role": "user", "content": pergunta})
    
    produtos_memoria = memoria.get("ultimos_produtos", [])

    if is_encerramento(texto_baixo):
        limpar_memoria()
        return {"resposta": "", "resultados": [], "acao": "ENCERRAR"}

    if is_pedido_resumo_rotas(texto_baixo) and memoria["produtos_mencionados"]:
        produtos_rota = produtos_por_secao(memoria["produtos_mencionados"].values())
        if produtos_rota:
            if idioma == "pt":
                resposta_texto = f"Montei um resumo com {len(produtos_rota)} rota(s) para as seções dos produtos que vimos."
            else:
                resposta_texto = f"I prepared a summary with {len(produtos_rota)} route(s) for the sections we discussed."
            memoria["historico_conversas"].append({"role": "assistant", "content": resposta_texto})
            return {"resposta": resposta_texto, "resultados": produtos_rota, "acao": "ABRIR_ROTAS"}

    analise = await classificar_intencao(pergunta, idioma)
    intencao = analise.get("intencao", "OUTROS")
    palavras = analise.get("palavras_chave", [])

    if intencao == "ENCERRAR":
        limpar_memoria()
        return {"resposta": "", "resultados": [], "acao": "ENCERRAR"}

    if produtos_memoria and (intencao == "IR_PARA_MAPA" or is_pedido_mapa(texto_baixo)):
        produtos_mapa = selecionar_produtos_para_mapa(texto_baixo, produtos_memoria)
        produtos_rota = produtos_por_secao(produtos_mapa)
        if len(produtos_rota) > 1:
            resposta_texto = f"Mostrando {len(produtos_rota)} rotas no mapa." if idioma == "pt" else f"Showing {len(produtos_rota)} routes on the map."
            memoria["historico_conversas"].append({"role": "assistant", "content": resposta_texto})
            return {"resposta": resposta_texto, "resultados": produtos_rota, "acao": "ABRIR_ROTAS"}

        produto_mapa = produtos_rota[0] if produtos_rota else produtos_memoria[0]
        resposta_texto = "Mostrando o caminho no mapa." if idioma == "pt" else "Showing the route on the map."
        memoria["historico_conversas"].append({"role": "assistant", "content": resposta_texto})
        return {"resposta": resposta_texto, "resultados": [produto_mapa], "acao": "ABRIR_MAPA"}

    if intencao == "SOBRE_PRODUTO" and not produtos_memoria:
        intencao = "NOVA_BUSCA"
        palavras = extrair_palavras_busca(texto_baixo)

    print(f"Intencao: {intencao} | Palavras: {palavras}")

    if intencao == "NOVA_BUSCA":
        resultados = buscar_produtos_sql(palavras)
        if resultados:
            memoria["ultimos_produtos"] = resultados[:3]
            memoria["assunto_ativo"] = "produto"
            
            # Adiciona ao dicionário de produtos mencionados
            for p in resultados[:3]:
                memoria["produtos_mencionados"][p["id"]] = p
                
            contexto = "Produtos encontrados no banco de dados:\n" + "\n---\n".join(
                [formatar_produto_para_contexto(p) for p in resultados[:3]]
            )
            todos_prods = list(memoria["produtos_mencionados"].values())
            resposta = await perguntar_llm(
                pergunta,
                contexto_produtos=contexto,
                idioma=idioma,
                historico=memoria["historico_conversas"][:-1],
                todos_produtos=todos_prods
            )
            memoria["historico_conversas"].append({"role": "assistant", "content": resposta})
            return {"resposta": resposta, "resultados": resultados[:3], "acao": "MOSTRAR_PRODUTOS"}

        memoria["ultimos_produtos"] = []
        memoria["assunto_ativo"] = None
        resposta_base = "Nenhum produto encontrado no banco de dados com esses termos. Informe ao usuario."
        todos_prods = list(memoria["produtos_mencionados"].values())
        resposta = await perguntar_llm(
            pergunta,
            contexto_produtos=resposta_base,
            idioma=idioma,
            historico=memoria["historico_conversas"][:-1],
            todos_produtos=todos_prods
        )
        memoria["historico_conversas"].append({"role": "assistant", "content": resposta})
        return {"resposta": resposta, "resultados": [], "acao": "NENHUM"}

    if intencao == "SOBRE_PRODUTO":
        produtos_relevantes = []
        palavras_pergunta = texto_baixo.split()
        for produto in produtos_memoria:
            nome_partes = produto["nome"].lower().split()
            if any(parte in palavras_pergunta for parte in nome_partes):
                produtos_relevantes.append(produto)

        final_context = produtos_relevantes if produtos_relevantes else produtos_memoria
        return await responder_sobre_produtos(pergunta, final_context, idioma)

    if intencao == "IR_PARA_MAPA":
        if produtos_memoria:
            produtos_mapa = selecionar_produtos_para_mapa(texto_baixo, produtos_memoria)
            produtos_rota = produtos_por_secao(produtos_mapa)
            if len(produtos_rota) > 1:
                resposta_texto = f"Mostrando {len(produtos_rota)} rotas no mapa." if idioma == "pt" else f"Showing {len(produtos_rota)} routes on the map."
                memoria["historico_conversas"].append({"role": "assistant", "content": resposta_texto})
                return {"resposta": resposta_texto, "resultados": produtos_rota, "acao": "ABRIR_ROTAS"}

            produto_mapa = produtos_rota[0] if produtos_rota else produtos_memoria[0]
            resposta_texto = "Mostrando o caminho no mapa." if idioma == "pt" else "Showing the route on the map."
            memoria["historico_conversas"].append({"role": "assistant", "content": resposta_texto})
            return {"resposta": resposta_texto, "resultados": [produto_mapa], "acao": "ABRIR_MAPA"}

        resposta_texto = "Qual produto voce gostaria de ver no mapa?" if idioma == "pt" else "Which product would you like to see on the map?"
        memoria["historico_conversas"].append({"role": "assistant", "content": resposta_texto})
        return {"resposta": resposta_texto, "resultados": [], "acao": "NENHUM"}

    if intencao != "OUTROS" and produtos_memoria:
        return await responder_sobre_produtos(pergunta, produtos_memoria, idioma)

    contexto = "Conversa casual ou duvida geral. Responda naturalmente como assistente de uma loja de roupas."
    todos_prods = list(memoria["produtos_mencionados"].values())
    resposta = await perguntar_llm(
        pergunta,
        contexto_produtos=contexto,
        idioma=idioma,
        historico=memoria["historico_conversas"][:-1],
        todos_produtos=todos_prods
    )
    memoria["historico_conversas"].append({"role": "assistant", "content": resposta})
    return {"resposta": resposta, "resultados": [], "acao": "NENHUM"}

