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
    # Busca por palavra inteira (evita "vestido" bater em "revestido" ou na descricao de outro produto)
    palavras = set(texto.replace("-", " ").split())
    return any(variante in palavras for variante in variantes)


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
        "voce", "voces", "disponivel", "disponiveis", "produto", "produtos", "outro",
        "outros", "outra", "outras", "opcao", "opcoes", "qual", "quais",
        "perfeito", "legal", "beleza", "certo", "ok", "entendi", "bom", "boa",
        "roupa", "roupas", "algum", "alguns", "alguma", "algumas", "hoje", "noite",
        "tudo", "bem", "vou", "numa", "num", "para", "pra",
    }
    sinonimos = {
        "short": "bermuda",
        "shorts": "bermuda",
        "bermudao": "bermuda",
        "bole": "bone",    # typo comum de "boné"
        "tenis": "tenis",  # garante normalizacao
        "bone": "bone",
    }
    return [
        sinonimos.get(normalizar_texto(palavra.strip(".,?!")), normalizar_texto(palavra.strip(".,?!")))
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
    if not tokens_sem_genero and not genero:
        return []

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


def listar_amostra_catalogo(limite=6):
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM produtos
        ORDER BY CAST(corredor AS INTEGER), nome
        """
    )
    produtos = cursor.fetchall()
    conn.close()
    return produtos_por_secao([formatar_produto(p) for p in produtos])[:limite]


def listar_todos_produtos_formatados():
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM produtos ORDER BY CAST(corredor AS INTEGER), nome")
    produtos = cursor.fetchall()
    conn.close()
    return [formatar_produto(p) for p in produtos]


def is_pedido_por_occasiao(texto_baixo):
    texto = normalizar_texto(texto_baixo)
    termos_ocasiao = [
        "festa", "sair", "saida", "noite", "balada", "evento", "encontro", "passeio",
        "frio", "calor", "trabalho", "casual", "presente",
    ]
    tem_contexto_roupa = any(termo in texto for termo in ["roupa", "roupas", "look", "opcao", "opcoes", "usar", "vestir"])
    return tem_contexto_roupa and any(termo in texto for termo in termos_ocasiao)


def buscar_produtos_por_occasiao(texto_baixo, limite=4):
    texto = normalizar_texto(texto_baixo)
    todos = listar_todos_produtos_formatados()

    if any(termo in texto for termo in ["festa", "sair", "saida", "noite", "balada", "evento", "encontro"]):
        prioridades = ["vestido", "camisa", "calca", "sandalia", "tenis", "saia", "polo"]
    elif "frio" in texto:
        prioridades = ["casaco", "moletom", "touca", "calca"]
    elif "calor" in texto or "passeio" in texto:
        prioridades = ["bermuda", "camisa", "saia", "sandalia", "bone", "oculos"]
    elif "trabalho" in texto:
        prioridades = ["camisa", "polo", "calca", "cinto", "sapato"]
    else:
        prioridades = ["camisa", "calca", "vestido", "tenis"]

    def combina_prioridade(produto, prioridade):
        texto_principal = normalizar_texto(
            " ".join(
                str(produto.get(campo, ""))
                for campo in ["nome", "tipo", "sku", "descricao"]
            ).replace("_", " ")
        )
        return prioridade in texto_principal

    escolhidos = []
    secoes_usadas = set()
    for prioridade in prioridades:
        for produto in todos:
            if produto["id"] in {p["id"] for p in escolhidos}:
                continue
            if not combina_prioridade(produto, prioridade):
                continue
            if produto.get("corredor") in secoes_usadas and len(escolhidos) < 3:
                continue
            escolhidos.append(produto)
            secoes_usadas.add(produto.get("corredor"))
            break
        if len(escolhidos) >= limite:
            break

    return escolhidos or listar_amostra_catalogo(limite)


def is_pedido_catalogo(texto_baixo):
    texto = normalizar_texto(texto_baixo)
    termos_catalogo = ["produto", "produtos", "opcao", "opcoes", "mais", "outro", "outros", "quais"]
    return any(termo in texto for termo in termos_catalogo) and not is_pedido_mapa(texto_baixo)


def is_pedido_catalogo_geral(texto_baixo):
    if not is_pedido_catalogo(texto_baixo):
        return False
    tokens = limpar_tokens_busca(extrair_palavras_busca(texto_baixo))
    return not tokens


def is_pergunta_pagamento(texto_baixo):
    texto = normalizar_texto(texto_baixo)
    termos_pagamento = ["boleto", "pix", "cartao", "credito", "debito", "parcelar", "pagamento", "pagar"]
    return any(termo in texto for termo in termos_pagamento)


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
        "me mostre",
        "quero ver",
        "ver",
        "ok",
        "ta",
        "vai",
        "vamos",
        "bora",
        "perfeito",
        "otimo",
        "gostei",
        "gostei sim",
        "adorei",
        "legal",
        "beleza",
        "show",
        "certo",
        "entendido",
    }
    return (
        texto in afirmacoes
        or "mapa" in texto
        or "onde" in texto
        or "caminho" in texto
        or "corredor" in texto
        or "localizacao" in texto
        or "me leva" in texto
        or "me indica" in texto
    )


def is_confirmacao_positiva(texto_baixo):
    """Detecta respostas afirmativas curtas que, combinadas com produtos na memória, indicam que o usuário quer ver o mapa."""
    texto = normalizar_texto(texto_baixo).replace(",", "").replace(".", "").replace("?", "").strip()
    afirmacoes = {
        "sim", "sim por favor", "por favor", "pode", "pode sim", "quero", "quero sim",
        "claro", "ok", "ta", "vai", "vamos", "bora", "perfeito", "otimo", "gostei",
        "gostei sim", "adorei", "legal", "beleza", "show", "certo", "entendido",
        "quero ver", "me mostra", "me mostre", "mostra", "mostre", "ver",
    }
    return texto in afirmacoes


def is_pedido_resumo_rotas(texto_baixo):
    texto = normalizar_texto(texto_baixo)
    # Detecta pedidos explícitos de rotas/resumo com múltiplos produtos
    tem_rota = any(palavra in texto for palavra in [
        "rota", "rotas", "mapa", "lugares", "secoes", "sessao", "resumo",
        "ver tudo", "ver todos", "todos os lugares", "todas as secoes",
    ])
    tem_total = any(palavra in texto for palavra in [
        "todos", "todas", "tudo", "geral", "resumo", "final",
        "falamos", "vimos", "conversamos", "mencionados", "vistos",
    ])
    # Detecta frases naturais como "onde ficam todos", "me mostra tudo no mapa"
    frases_naturais = [
        "onde ficam", "onde estao", "onde sao", "onde fica tudo",
        "me mostra tudo", "mostrar tudo", "ver tudo no mapa",
        "todos no mapa", "tudo no mapa", "mapa de tudo",
        "quero ver todos", "quero ver tudo", "onde tem tudo",
        "como chegar em todos", "caminho de todos",
    ]
    return (tem_rota and tem_total) or any(frase in texto for frase in frases_naturais)


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
        "elas", "eles", "ele", "ela", "gostei", "sim", "tudo", "todos", "todas", "falamos",
        "vimos", "conversamos",
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
        "perfeito", "legal", "beleza", "certo", "ok", "entendi", "bom", "boa",
        "roupa", "roupas", "algum", "alguns", "alguma", "algumas", "hoje", "noite",
        "tudo", "bem", "vou", "numa", "num", "para", "pra",
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


async def responder_catalogo_geral(pergunta, idioma):
    produtos = listar_amostra_catalogo(7)
    for produto in produtos:
        memoria["produtos_mencionados"][produto["id"]] = produto
    memoria["ultimos_produtos"] = produtos[:3]
    memoria["assunto_ativo"] = "produto"

    contexto = (
        "O usuario fez uma pergunta geral ou mal formulada sobre quais produtos existem na loja. "
        "Interprete como pedido de continuidade do catalogo. Responda naturalmente, mencione as secoes "
        "disponiveis e alguns exemplos reais abaixo. Nao diga que nenhum produto foi encontrado.\n"
        + "\n---\n".join([formatar_produto_para_contexto(p) for p in produtos])
    )
    todos_prods = list(memoria["produtos_mencionados"].values())
    resposta = await perguntar_llm(
        pergunta,
        contexto_produtos=contexto,
        idioma=idioma,
        historico=memoria["historico_conversas"][:-1],
        todos_produtos=todos_prods,
    )
    memoria["historico_conversas"].append({"role": "assistant", "content": resposta})
    return {"resposta": resposta, "resultados": produtos, "acao": "MOSTRAR_PRODUTOS"}


async def responder_por_occasiao(pergunta, idioma):
    produtos = buscar_produtos_por_occasiao(pergunta)
    memoria["ultimos_produtos"] = produtos[:3]
    memoria["assunto_ativo"] = "produto"
    for produto in produtos:
        memoria["produtos_mencionados"][produto["id"]] = produto

    contexto = (
        "O usuario descreveu uma ocasiao ou uso da roupa, nao um produto exato. "
        "Interprete a intencao e sugira produtos reais do banco que combinem com a situacao. "
        "Fale de forma natural e objetiva, sem dizer que nenhum produto foi encontrado.\n"
        + "\n---\n".join([formatar_produto_para_contexto(p) for p in produtos])
    )
    resposta = await perguntar_llm(
        pergunta,
        contexto_produtos=contexto,
        idioma=idioma,
        historico=memoria["historico_conversas"][:-1],
        todos_produtos=list(memoria["produtos_mencionados"].values()),
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

    if is_pergunta_pagamento(texto_baixo):
        resposta_texto = (
            "Sobre pagamento, eu consigo te ajudar melhor com os produtos e a localização deles. "
            "Formas como boleto, Pix ou cartão precisam ser confirmadas no caixa da loja."
            if idioma == "pt"
            else "For payment, I can best help with products and their location. Methods like bank slip, Pix, or card should be confirmed at checkout."
        )
        memoria["historico_conversas"].append({"role": "assistant", "content": resposta_texto})
        return {"resposta": resposta_texto, "resultados": [], "acao": "NENHUM"}

    if is_pedido_resumo_rotas(texto_baixo) and memoria["produtos_mencionados"]:
        produtos_rota = produtos_por_secao(memoria["produtos_mencionados"].values())
        if produtos_rota:
            if idioma == "pt":
                resposta_texto = f"Claro! Aqui estão as {len(produtos_rota)} seção(ões) dos produtos que conversamos."
            else:
                resposta_texto = f"Sure! Here are the {len(produtos_rota)} section(s) for the products we discussed."
            memoria["historico_conversas"].append({"role": "assistant", "content": resposta_texto})
            return {"resposta": resposta_texto, "resultados": produtos_rota, "acao": "ABRIR_ROTAS"}

    # Detecção de confirmação positiva contextual: usuário responde afirmativamente a uma sugestão de mapa
    # Ex: "sim", "perfeito", "gostei", "quero ver" — quando já tem produtos na memória
    ultima_resposta_ia = ""
    if memoria["historico_conversas"]:
        # Pega a última mensagem do assistente (antes da atual do usuário)
        msgs_assistente = [m for m in memoria["historico_conversas"][:-1] if m["role"] == "assistant"]
        if msgs_assistente:
            ultima_resposta_ia = normalizar_texto(msgs_assistente[-1]["content"])

    ia_ofereceu_mapa = any(termo in ultima_resposta_ia for termo in [
        "mapa", "localizacao", "caminho", "corredor", "mostrar", "onde", "rota"
    ])

    if is_confirmacao_positiva(texto_baixo) and ia_ofereceu_mapa and produtos_memoria:
        todos_mencionados = list(memoria["produtos_mencionados"].values())
        pool_mapa = todos_mencionados if todos_mencionados else produtos_memoria
        produtos_rota = produtos_por_secao(pool_mapa)
        if len(produtos_rota) > 1:
            resposta_texto = f"Ótimo! Mostrando {len(produtos_rota)} rotas no mapa." if idioma == "pt" else f"Great! Showing {len(produtos_rota)} routes on the map."
            memoria["historico_conversas"].append({"role": "assistant", "content": resposta_texto})
            return {"resposta": resposta_texto, "resultados": produtos_rota, "acao": "ABRIR_ROTAS"}
        produto_mapa = produtos_rota[0] if produtos_rota else produtos_memoria[0]
        resposta_texto = "Ótimo! Mostrando o caminho no mapa." if idioma == "pt" else "Great! Showing the route on the map."
        memoria["historico_conversas"].append({"role": "assistant", "content": resposta_texto})
        return {"resposta": resposta_texto, "resultados": [produto_mapa], "acao": "ABRIR_MAPA"}

    if is_pedido_catalogo_geral(texto_baixo):
        return await responder_catalogo_geral(pergunta, idioma)

    if is_pedido_por_occasiao(texto_baixo):
        return await responder_por_occasiao(pergunta, idioma)

    analise = await classificar_intencao(pergunta, idioma)
    intencao = analise.get("intencao", "OUTROS")
    palavras = analise.get("palavras_chave", [])

    if intencao == "ENCERRAR":
        limpar_memoria()
        return {"resposta": "", "resultados": [], "acao": "ENCERRAR"}

    if produtos_memoria and (intencao == "IR_PARA_MAPA" or is_pedido_mapa(texto_baixo)):
        # Usa todos os produtos já mencionados na sessão, não só os últimos
        todos_mencionados = list(memoria["produtos_mencionados"].values())
        pool_mapa = todos_mencionados if todos_mencionados else produtos_memoria
        produtos_mapa = selecionar_produtos_para_mapa(texto_baixo, produtos_memoria)
        # Se a frase é genérica/afirmativa, mostra todas as seções da sessão
        if is_confirmacao_positiva(texto_baixo) or is_pedido_resumo_rotas(texto_baixo):
            produtos_mapa = pool_mapa
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
        if is_pedido_por_occasiao(texto_baixo) or is_pedido_catalogo(texto_baixo):
            return await responder_por_occasiao(pergunta, idioma)

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

