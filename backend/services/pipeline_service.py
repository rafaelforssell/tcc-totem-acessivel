import os
import re
import unicodedata

from services.llm_service import classificar_intencao, perguntar_llm
from services import db_service


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

memoria = {
    "ultimos_produtos": [],
    "assunto_ativo": None,
    "historico_conversas": [],
    "produtos_mencionados": {},
    "produtos_escolhidos": [],
    "produtos_pendentes_confirmacao": [],
}


def limpar_memoria():
    memoria["ultimos_produtos"] = []
    memoria["assunto_ativo"] = None
    memoria["historico_conversas"] = []
    memoria["produtos_mencionados"] = {}
    memoria["produtos_escolhidos"] = []
    memoria["produtos_pendentes_confirmacao"] = []
    memoria["tentativas_silencio"] = 0
    memoria["genero"] = None
    memoria["tipo_ativo"] = None


def conectar_bd():
    """Mantido por compatibilidade com outros módulos que possam importá-lo."""
    import sqlite3
    sqlite_path = os.path.join(BASE_DIR, "..", "..", "database", "produtos.db")
    conn = sqlite3.connect(sqlite_path)
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
            for campo in ["nome", "categoria", "tipo", "cor", "tamanho", "marca", "descricao", "sku", "setor"]
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
    if any(palavra in texto for palavra in ["feminino", "feminina", "femininos", "femininas", "fem", "mulher", "mulheres"]):
        return "fem"
    if any(palavra in texto for palavra in ["masculino", "masculina", "masculinos", "masculinas", "masc", "mas", "homem", "homens"]):
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


def limpar_tokens_busca(palavras_chave, palavras_validas=None):
    stopwords = {
        "eu", "quero", "queria", "saber", "mais", "sobre", "a", "o", "as", "os",
        "de", "da", "do", "tem", "ha", "me", "fale", "uma", "um", "por", "favor",
        "voce", "você", "voces", "disponivel", "disponiveis", "produto", "produtos", "outro",
        "outros", "outra", "outras", "opcao", "opcoes", "qual", "quais",
        "perfeito", "legal", "beleza", "certo", "ok", "entendi", "bom", "boa",
        "roupa", "roupas", "algum", "alguns", "alguma", "algumas", "hoje", "noite",
        "tudo", "bem", "vou", "numa", "num", "para", "pra",
        "nao", "sim", "gostei", "agora", "entao", "quer", "quero", "temos",
        "pode", "poderia", "mostra", "mostrar", "mostre", "ver", "loja",
        "nessa", "nesta", "encontra", "encontrar", "acha", "achar",
        "acho", "que", "dos", "das", "duas", "dois", "ambos", "ambas",
        "eles", "elas", "usar", "uso", "usando", "fechar", "so",
        "esta", "está", "estao", "estão", "estou", "estava", "este", "estes", "estas",
        "onde", "como",
        # Stopwords de ação de compras e experimentação
        "comprar", "compra", "compras", "buscar", "busca", "procurar", "procura",
        "adquirir", "pegar", "levar", "olhar", "consigo", "experimentar", "provar", "vestir", "trocar",
        # Palavras de pessoa / relacionamento — NUNCA são produtos
        "namorada", "namorado", "esposa", "esposo", "marido", "mulher",
        "mae", "pai", "filho", "filha", "irma", "irmao", "amiga", "amigo",
        "prima", "primo", "tia", "tio", "avo", "avoa", "neta", "neto",
        "pessoa", "pessoas", "alguem", "ninguem", "minha", "meu", "sua", "seu",
        "ela", "ele", "nos", "presente", "presentear",
        # Palavras de ocasião/tempo
        "aniversario", "aniversário", "festa", "festas", "casamento", "casamentos",
        "trabalho", "academia", "noite", "noites", "dia", "dias", "presente",
        "presentes", "presentear", "amanha", "amanhã", "ontem", "hoje", "balada",
        "baladas", "evento", "eventos", "encontro", "encontros", "passeio",
        "passeios", "casual", "casuais",
    }
    sinonimos = {
        "short": "bermuda",
        "shorts": "bermuda",
        "bermudao": "bermuda",
        "bole": "bone",    # typo comum de "boné"
        "tenis": "tenis",  # garante normalizacao
        "bone": "bone",
        "camiseta": "camisa",
        "camisetas": "camisa",
    }
    
    limpos = []
    for palavra in palavras_chave:
        p_clean = normalizar_texto(palavra.strip(".,?!"))
        
        # Singulariza tipos conhecidos terminados em 's' (ex: camisas -> camisa)
        if len(p_clean) > 3 and p_clean.endswith("s"):
            p_sing = p_clean[:-1]
            if p_sing in TIPOS_CONHECIDOS:
                p_clean = p_sing

        is_tamanho = p_clean in TAMANHOS_CONHECIDOS
        if (len(p_clean) <= 2 and not is_tamanho) or p_clean in stopwords:
            continue
        p_norm = sinonimos.get(p_clean, p_clean)
        
        # Se temos palavras válidas da IA, filtramos tipos conhecidos que não estejam nas válidas
        if palavras_validas is not None:
            # Verifica se é um tipo conhecido
            is_tipo = p_norm in TIPOS_CONHECIDOS or (len(p_norm) > 3 and p_norm.endswith("s") and p_norm[:-1] in TIPOS_CONHECIDOS)
            if is_tipo:
                # Se for tipo, tem que bater com alguma palavra válida
                match_valida = False
                for v in palavras_validas:
                    v_norm = normalizar_texto(v)
                    v_sing = v_norm[:-1] if (len(v_norm) > 3 and v_norm.endswith("s")) else v_norm
                    p_sing = p_norm[:-1] if (len(p_norm) > 3 and p_norm.endswith("s")) else p_norm
                    if p_sing == v_sing:
                        match_valida = True
                        break
                if not match_valida:
                    # Ignora este tipo pois não foi extraído pela IA
                    continue
        limpos.append(p_norm)
    return limpos


TIPOS_CONHECIDOS = {
    "bone", "vestido", "casaco", "camisa", "calca", "bermuda", "tenis", "sandalia",
    "saia", "oculos", "garrafa", "cinto", "moletom", "touca", "polo", "camiseta",
}

CORES_CONHECIDAS = {
    "preto", "preta", "branco", "branca", "vermelho", "vermelha", "azul", "verde",
    "marrom", "cinza", "bege", "jeans",
}

TAMANHOS_CONHECIDOS = {
    "p", "m", "g", "gg", "pp", "xg", "xxg", "unico",
    "34", "36", "38", "40", "42", "44", "46", "48", "50",
    "35", "37", "39", "41", "43", "45"
}

TOKENS_GENERO = {
    "feminino", "feminina", "femininos", "femininas", "fem", "mulher", "mulheres",
    "masculino", "masculina", "masculinos", "masculinas", "masc", "mas", "homem", "homens"
}


def extrair_segmentos_busca(texto_baixo, palavras_validas=None):
    texto = normalizar_texto(texto_baixo)
    for tipo in sorted(TIPOS_CONHECIDOS, key=len, reverse=True):
        texto = re.sub(rf"\b(?:um|uma|o|a)\s+({tipo})\b", r", \1", texto)
    partes = re.split(r"\s*(?:,|;|\b(?:e|ou|com)\b)\s*", texto)
    segmentos = []
    for parte in partes:
        tokens = limpar_tokens_busca(parte.split(), palavras_validas)
        if tokens:
            segmentos.append(tokens)
    return segmentos


def obter_tipo_segmento(tokens):
    for token in tokens:
        if token in TIPOS_CONHECIDOS:
            return token
        if len(token) > 3 and token.endswith("s") and token[:-1] in TIPOS_CONHECIDOS:
            return token[:-1]
    return None


def ordenar_por_aderencia(produtos, tipo_base=None, atributos=None):
    atributos = atributos or []
    ordenados = sorted(
        produtos,
        key=lambda p: (
            -sum(1 for atributo in atributos if token_match(texto_produto(p), atributo)),
            0 if tipo_base and token_match(texto_produto(p), tipo_base) else 1,
            normalizar_texto(obter_campo(p, "nome")),
        )
    )
    return ordenados


def buscar_produtos_por_segmentos(texto_baixo, palavras_validas=None):
    segmentos = extrair_segmentos_busca(texto_baixo, palavras_validas)
    if not segmentos:
        return None

    todos_produtos_raw = db_service.fetchall("SELECT * FROM produtos ORDER BY nome, cor, tamanho")
    com_estoque = [p for p in todos_produtos_raw if (p.get("estoque") or 0) > 0]

    genero = memoria.get("genero")

    resultados = []
    faltas = []
    ids_escolhidos = set()

    for tokens in segmentos:
        tokens_sem_genero = [t for t in tokens if t not in TOKENS_GENERO]
        if not tokens_sem_genero:
            continue
        tipo = obter_tipo_segmento(tokens_sem_genero)
        atributos = [token for token in tokens_sem_genero if token != tipo]

        candidatos_exatos = []
        for produto in com_estoque:
            if genero and genero_produto(produto) != genero:
                continue
            texto = texto_produto(produto)
            if all(token_match(texto, token) for token in tokens_sem_genero):
                candidatos_exatos.append(produto)

        if candidatos_exatos:
            escolhidos = ordenar_por_aderencia(candidatos_exatos, tipo, atributos)
            for produto in escolhidos:
                produto_id = obter_campo(produto, "id", 0)
                if produto_id not in ids_escolhidos:
                    resultados.append(formatar_produto(produto))
                    ids_escolhidos.add(produto_id)
                    if len(segmentos) > 1 or len(resultados) >= 3:
                        break
            continue

        if not tipo:
            continue

        candidatos_tipo = []
        for produto in com_estoque:
            if genero and genero_produto(produto) != genero:
                continue
            texto = texto_produto(produto)
            if token_match(texto, tipo):
                candidatos_tipo.append(produto)

        if not candidatos_tipo:
            continue

        escolhidos = ordenar_por_aderencia(candidatos_tipo, tipo, atributos)
        produto_referencia_falta = escolhidos[0] if escolhidos else None
        for produto in escolhidos:
            produto_id = obter_campo(produto, "id", 0)
            if produto_id not in ids_escolhidos:
                resultados.append(formatar_produto(produto))
                ids_escolhidos.add(produto_id)
                produto_referencia_falta = produto
                if len(segmentos) > 1 or len(resultados) >= 3:
                    break

        texto_referencia = texto_produto(produto_referencia_falta) if produto_referencia_falta else ""
        faltando = [
            token for token in atributos
            if (token in CORES_CONHECIDAS or token not in {"fem", "mas"})
            and not token_match(texto_referencia, token)
        ]
        if faltando:
            faltas.append({"tipo": tipo, "atributos": faltando})

    if not resultados and not faltas:
        return None

    return {
        "produtos": resultados[:3],
        "faltas": faltas,
        "segmentos_total": len(segmentos),
        "segmentos_encontrados": len(resultados[:3]),
    }


def montar_resposta_busca_natural(produtos, faltas=None, idioma="pt"):
    faltas = faltas or []
    nomes = [p.get("nome", "Produto") for p in produtos[:3]]

    if idioma != "pt":
        if faltas:
            avisos = []
            for falta in faltas:
                atributos = " ".join(falta["atributos"])
                avisos.append(f"I couldn't find {falta['tipo']} in {atributos}")
            if not nomes:
                return f"{'. '.join(avisos)}. If you want, I can look for something similar."
            return f"{'. '.join(avisos)}. I found these similar options: {', '.join(nomes)}. Do any of them work for you?"
        if len(nomes) == 1:
            return f"I found this option for you: {nomes[0]}. What do you think?"
        return f"I found these options for you: {', '.join(nomes)}. Do any of them work for you?"

    if faltas:
        avisos = []
        for falta in faltas:
            atributos = " ".join(falta["atributos"])
            avisos.append(f"Nao encontrei {falta['tipo']} {atributos}".strip())
        if not nomes:
            return f"{'. '.join(avisos)}. Se quiser, eu posso procurar algo parecido para voce."
        return f"{'. '.join(avisos)}. Separei estas opcoes parecidas para voce: {', '.join(nomes)}. Alguma delas te agradou?"

    if len(nomes) == 1:
        return f"Encontrei esta opcao para voce: {nomes[0]}. O que achou?"
    return f"Encontrei estas opcoes para voce: {', '.join(nomes)}. Alguma delas te agradou?"


def is_confirmacao_lista(texto_baixo):
    texto = normalizar_texto(texto_baixo).replace(",", "").replace(".", "").replace("?", "").strip()
    confirmacoes = {
        "sim", "sim gostei", "gostei", "gostei sim", "adorei", "perfeito", "pode ser",
        "esse", "essa", "esses", "essas", "quero esse", "quero essa", "levei", "vou querer",
        "pode colocar", "coloca", "coloque", "quero", "quero por favor", "quero esses", "quero essas",
        "gostei das duas", "gostei dos dois", "gostei de ambas", "gostei de ambos",
        "quero as duas", "quero os dois", "as duas", "os dois",
    }
    return texto in confirmacoes


def montar_resposta_mapa(produtos, idioma="pt"):
    total = len(produtos or [])
    if idioma != "pt":
        if total > 1:
            return f"Sure, I'll show the route for the {total} products on the map."
        return "Sure, I'll show the route on the map."
    if total > 1:
        return f"Certo, vou te mostrar no mapa onde estao os {total} produtos."
    return "Certo, vou te mostrar no mapa onde ele fica."


def is_negacao_curta(texto_baixo):
    texto = normalizar_texto(texto_baixo).replace(",", "").replace(".", "").replace("?", "").strip()
    return texto in {"nao", "nao gostei", "nao quero", "nenhum", "nenhuma", "outra opcao", "outras opcoes"}


def montar_resposta_multiplos_produtos(produtos, idioma="pt"):
    nomes = [p.get("nome", "Produto") for p in produtos[:3]]
    if idioma != "pt":
        return f"I found these options for you: {', '.join(nomes)}. Do any of them work for you?"
    return f"Encontrei estas opcoes para voce: {', '.join(nomes)}. Alguma delas te agradou?"


def buscar_produtos_sql(palavras_chave):
    if not palavras_chave:
        return []

    # Se nao houver nenhum tipo conhecido nas palavras_chave, e houver tipo_ativo na memoria, herda-o
    tokens = limpar_tokens_busca(palavras_chave)
    tem_tipo = any(t.lower() in TIPOS_CONHECIDOS or (len(t) > 3 and t.lower().endswith("s") and t.lower()[:-1] in TIPOS_CONHECIDOS) for t in tokens)
    if not tem_tipo and memoria.get("tipo_ativo"):
        tipo_herdado = memoria["tipo_ativo"]
        if tipo_herdado.lower() not in [t.lower() for t in tokens]:
            palavras_chave = list(palavras_chave) + [tipo_herdado]

    todos_produtos_raw = db_service.fetchall(
        "SELECT * FROM produtos ORDER BY nome, cor, tamanho"
    )

    tokens = limpar_tokens_busca(palavras_chave)
    genero = detectar_genero(tokens) or memoria.get("genero")
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

    def selecionar_por_token(produtos_base):
        escolhidos = []
        ids_escolhidos = set()
        secoes_usadas = set()

        for token in tokens_sem_genero:
            candidatos = [p for p in produtos_base if token_match(texto_produto(p), token)]
            if not candidatos:
                continue

            candidatos.sort(
                key=lambda p: (
                    p.get("corredor") in secoes_usadas,
                    normalizar_texto(obter_campo(p, "nome")),
                )
            )
            escolhido = candidatos[0]
            produto_id = obter_campo(escolhido, "id", 0)
            if produto_id in ids_escolhidos:
                continue

            escolhidos.append(escolhido)
            ids_escolhidos.add(produto_id)
            secoes_usadas.add(obter_campo(escolhido, "corredor", 10))

        return escolhidos

    # Separa produtos com e sem estoque
    com_estoque = [p for p in todos_produtos_raw if (p.get("estoque") or 0) > 0]
    sem_estoque = [p for p in todos_produtos_raw if (p.get("estoque") or 0) <= 0]

    # 1. Busca exata (todos os tokens batem) com estoque primeiro
    produtos = [p for p in com_estoque if produto_valido(p, exigir_todos=True)]
    if produtos:
        return [formatar_produto(p) for p in produtos]

    # 2. Se nao achou exata, mas tem multiplos tokens, tenta selecionar um de cada (busca multi-produto)
    if len(tokens_sem_genero) > 1:
        multi_resultados = selecionar_por_token(com_estoque)
        if len(multi_resultados) >= 2:
            return [formatar_produto(p) for p in multi_resultados]

    # 3. Busca parcial (qualquer token bate) com estoque
    produtos = [p for p in com_estoque if produto_valido(p, exigir_todos=False)]

    # 4. Se nao achou com estoque, verifica se existe esgotado para dar mensagem adequada
    if not produtos:
        esgotados = [p for p in sem_estoque if produto_valido(p, exigir_todos=True)]
        if not esgotados:
            esgotados = [p for p in sem_estoque if produto_valido(p, exigir_todos=False)]
        if esgotados:
            # Retorna marcado como esgotado para a IA dar a mensagem certa
            return [{**formatar_produto(p), "_esgotado": True} for p in esgotados[:3]]

    return [formatar_produto(p) for p in produtos]


def listar_amostra_catalogo(limite=6):
    genero = memoria.get("genero")
    produtos = db_service.fetchall(
        "SELECT * FROM produtos WHERE estoque > 0 ORDER BY corredor, nome"
    )
    if genero:
        produtos = [p for p in produtos if genero_produto(p) == genero]
    return produtos_por_secao([formatar_produto(p) for p in produtos])[:limite]


def listar_todos_produtos_formatados():
    genero = memoria.get("genero")
    produtos = db_service.fetchall(
        "SELECT * FROM produtos WHERE estoque > 0 ORDER BY corredor, nome"
    )
    if genero:
        produtos = [p for p in produtos if genero_produto(p) == genero]
    return [formatar_produto(p) for p in produtos]


def buscar_produtos_por_genero(genero, limite=4):
    produtos = [
        produto for produto in listar_todos_produtos_formatados()
        if genero_produto(produto) == genero
    ]
    return produtos_por_secao(produtos)[:limite]


def is_pedido_catalogo_por_genero(texto_baixo):
    texto = normalizar_texto(texto_baixo)
    genero = detectar_genero(texto.split())
    if not genero or is_pedido_mapa(texto):
        return False

    tokens = set(limpar_tokens_busca(texto.split()))
    tem_tipo_especifico = any(
        token in TIPOS_CONHECIDOS or (len(token) > 3 and token.endswith("s") and token[:-1] in TIPOS_CONHECIDOS)
        for token in tokens
    )
    if tem_tipo_especifico:
        return False

    termos_consulta = [
        "tem", "voces tem", "o que tem", "quais", "opcao", "opcoes",
        "produto", "produtos", "loja", "nessa loja", "nesta loja",
    ]
    return any(termo in texto for termo in termos_consulta)


async def responder_catalogo_por_genero(pergunta, idioma):
    genero = detectar_genero(normalizar_texto(pergunta).split())
    produtos = buscar_produtos_por_genero(genero)

    memoria["ultimos_produtos"] = produtos[:3]
    memoria["assunto_ativo"] = "produto" if produtos else None
    memoria["produtos_pendentes_confirmacao"] = produtos[:3]
    for produto in produtos[:3]:
        memoria["produtos_mencionados"][produto["id"]] = produto

    if produtos:
        nomes = ", ".join(produto["nome"] for produto in produtos[:3])
        if idioma == "pt":
            publico = "homem" if genero == "mas" else "mulher"
            resposta = f"Para {publico}, encontrei estas opcoes: {nomes}. Alguma delas te agradou?"
        else:
            publico = "men" if genero == "mas" else "women"
            resposta = f"For {publico}, I found these options: {nomes}. Do any of them work for you?"
        memoria["historico_conversas"].append({"role": "assistant", "content": resposta})
        return {"resposta": resposta, "resultados": produtos[:3], "acao": "MOSTRAR_PRODUTOS"}

    resposta = (
        "Nao encontrei produtos dessa secao com estoque agora. Posso procurar outro tipo de produto para voce."
        if idioma == "pt"
        else "I couldn't find in-stock products in that section right now. I can look for another type of product."
    )
    memoria["historico_conversas"].append({"role": "assistant", "content": resposta})
    return {"resposta": resposta, "resultados": [], "acao": "NENHUM"}


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


def is_pedido_provador(texto_baixo):
    texto = normalizar_texto(texto_baixo)
    termos = ["provador", "provadores", "vestiario", "experimentar", "provar", "vestir", "trocar", "cabine"]
    return any(t in texto for t in termos)


def is_pedido_caixa(texto_baixo):
    texto = normalizar_texto(texto_baixo)
    # Detecta se pergunta onde pagar, onde é o caixa, ou onde finalizar/efetuar a compra
    termos_onde = ["onde", "aonde", "como chego", "como ir", "caminho", "localizacao", "onde fica", "onde e"]
    if "caixa" in texto:
        return True
    if any(o in texto for o in termos_onde) and any(c in texto for c in ["pagar", "pagamento", "comprar", "compra", "finalizar", "efetuar"]):
        return True
    return False


def is_confirmacao_compra(texto_baixo):
    texto = normalizar_texto(texto_baixo)
    termos_compra = [
        "vou levar", "quero levar", "levar essas", "levar estes", "levar esses",
        "vou comprar", "quero comprar", "vou pegar", "quero pegar",
        "vou ficar com", "fico com", "fechado vou levar", "perfeito vou levar"
    ]
    return any(termo in texto for termo in termos_compra)


def texto_encerramento(idioma="pt"):
    return (
        "Obrigado por usar o Kiosk. Estou encerrando esta sessão e o totem será reiniciado em 10 segundos."
        if idioma == "pt"
        else "Thank you for using Kiosk. I am ending this session and the kiosk will restart in 10 seconds."
    )


def destino_caixa():
    return {
        "id": "caixa",
        "nome": "Caixas",
        "corredor": "9",
        "setor": "Caixas"
    }


def is_pergunta_pagamento(texto_baixo):
    texto = normalizar_texto(texto_baixo)
    termos_pagamento = ["boleto", "pix", "cartao", "credito", "debito", "parcelar", "pagamento", "pagar"]
    return any(termo in texto for termo in termos_pagamento)


def is_encerramento(texto_baixo):
    texto = normalizar_texto(texto_baixo).replace(",", " ").replace(".", " ").replace("?", " ")
    palavras = texto.split()
    despedidas = {
        "tchau", "thcau", "tcau", "tchao", "tchauu",
        "obrigado", "obrigada", "valeu", "encerrar", "bye", "thanks", "falou",
    }
    return (any(w in palavras for w in despedidas) or "ate logo" in texto) and len(palavras) <= 4


def is_pedido_atendente(texto_baixo):
    """Detecta quando o usuário pede ajuda humana/atendente."""
    texto = normalizar_texto(texto_baixo)
    termos = [
        "atendente", "atendimento", "funcionario", "vendedor", "vendedora",
        "chame", "chamar", "preciso de ajuda", "me ajuda", "ajuda humana",
        "falar com alguem", "falar com uma pessoa", "pessoa real",
        "nao consigo", "nao entendeu", "nao entendo", "chama alguem",
        "chama um atendente", "quero um atendente", "quero ajuda",
    ]
    return any(termo in texto for termo in termos)


def is_pedido_mapa(texto_baixo):
    texto = normalizar_texto(texto_baixo).replace(",", "").replace(".", "").replace("?", "").strip()
    pedidos_explicitos = {
        "abrir mapa",
        "abre o mapa",
        "abrir o mapa",
        "pode abrir o mapa",
        "mostra o mapa",
        "mostre o mapa",
        "mostrar mapa",
        "me mostra o mapa",
        "me mostre o mapa",
        "quero ver o mapa",
        "quero ver no mapa",
        "ver mapa",
        "ver no mapa",
    }
    return (
        texto in pedidos_explicitos
        or "mapa" in texto
        or "onde" in texto
        or "caminho" in texto
        or "corredor" in texto
        or "localizacao" in texto
        or "fica" in texto
        or "encontra" in texto
        or "chegar" in texto
        or "me leva" in texto
    )


def is_confirmacao_positiva(texto_baixo):
    """Detecta respostas afirmativas curtas que, combinadas com produtos na memória, indicam que o usuário quer ver o mapa."""
    texto = normalizar_texto(texto_baixo).replace(",", "").replace(".", "").replace("?", "").strip()
    afirmacoes = {
        "sim", "sim por favor", "por favor", "pode", "pode sim", "quero", "quero sim",
        "claro", "ok", "ta", "vai", "vamos", "bora", "perfeito", "otimo", "gostei",
        "gostei sim", "adorei", "legal", "beleza", "show", "certo", "entendido",
        "quero ver", "me mostra", "me mostre", "mostra", "mostre", "ver",
        "abrir", "abre", "pode abrir", "abre o mapa", "abrir o mapa",
    }
    return texto in afirmacoes


def ia_ofereceu_mapa_no_historico():
    msgs_assistente = [
        m for m in memoria.get("historico_conversas", [])[:-1]
        if m.get("role") == "assistant"
    ]
    if not msgs_assistente:
        return False

    ultima_resposta_ia = normalizar_texto(msgs_assistente[-1].get("content", ""))
    tem_mapa = any(termo in ultima_resposta_ia for termo in [
        "mapa", "localizacao", "caminho", "corredor", "mostrar", "onde", "rota"
    ])
    tem_convite = any(termo in ultima_resposta_ia for termo in [
        "quer", "gostaria", "deseja", "posso", "posso te", "quer que eu", "voce quer"
    ])
    return tem_mapa and tem_convite and "?" in ultima_resposta_ia


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
        "eles", "elas", "esses", "essas", "estes", "estas",
    ])
    # Detecta frases naturais como "onde ficam todos", "me mostra tudo no mapa"
    frases_naturais = [
        "onde ficam", "onde estao", "onde sao", "onde fica tudo",
        "me mostra tudo", "mostrar tudo", "ver tudo no mapa",
        "todos no mapa", "tudo no mapa", "mapa de tudo",
        "quero ver todos", "quero ver tudo", "onde tem tudo",
        "como chegar em todos", "caminho de todos",
        "mostrar eles", "mostra eles", "mostrar elas", "mostra elas",
        "mostrar esses", "mostra esses", "mostrar essas", "mostra essas",
    ]
    return (tem_rota and tem_total) or any(frase in texto for frase in frases_naturais)


def menciona_todos_os_produtos(texto_baixo):
    texto = normalizar_texto(texto_baixo)
    expressoes = [
        "os dois", "as duas", "ambos", "ambas",
        "os dois produtos", "as duas opcoes", "as duas opções",
        "os dois no mapa", "as duas no mapa",
        "todos eles", "todas elas",
    ]
    if any(expressao in texto for expressao in expressoes):
        return True
    
    palavras_plurais = {"eles", "elas", "esses", "essas", "estes", "estas"}
    if palavras_plurais.intersection(set(texto.split())):
        return True
        
    return False


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
        "vimos", "conversamos", "duas", "dois", "ambos", "ambas", "queria", "ver",
        "encontra", "encontrar", "loja", "poderia",
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
    return [produto for score, produto in pontuados if score == maior_score]


def extrair_palavras_busca(texto_baixo):
    stopwords = {
        "eu", "quero", "queria", "saber", "mais", "sobre", "a", "o", "as", "os",
        "de", "da", "do", "tem", "ha", "me", "fale", "uma", "um", "por", "favor",
        "perfeito", "legal", "beleza", "certo", "ok", "entendi", "bom", "boa",
        "roupa", "roupas", "algum", "alguns", "alguma", "algumas", "hoje", "noite",
        "tudo", "bem", "vou", "numa", "num", "para", "pra",
        "esta", "está", "estao", "estão", "estou", "estava", "este", "estes", "estas",
        "onde", "como", "voce", "você", "voces", "pode", "poderia", "gostei",
        # Stopwords de ação de compras e experimentação
        "comprar", "compra", "compras", "buscar", "busca", "procurar", "procura",
        "adquirir", "pegar", "levar", "olhar", "consigo", "experimentar", "provar", "vestir", "trocar",
    }
    return [
        normalizar_texto(w.strip(".,?!"))
        for w in texto_baixo.split()
        if (len(w.strip(".,?!")) > 2 or normalizar_texto(w.strip(".,?!")) in TAMANHOS_CONHECIDOS)
        and normalizar_texto(w.strip(".,?!")) not in stopwords
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
    memoria["produtos_pendentes_confirmacao"] = produtos[:3]

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
    memoria["produtos_pendentes_confirmacao"] = produtos[:3]
    for produto in produtos:
        memoria["produtos_mencionados"][produto["id"]] = produto

    contexto = (
        "O usuario descreveu uma ocasiao ou uso da roupa, nao um produto exato. "
        "Interprete a intencao e sugira produtos reais do banco que combinem com a situacao. "
        "Fale de forma natural e objetiva, sem dizer que nenhum produto foi encontrado.\n"
        + "\n---\n".join([formatar_produto_para_contexto(p) for p in produtos])
    )
    if len(produtos) > 1:
        resposta = montar_resposta_multiplos_produtos(produtos, idioma)
    else:
        resposta = await perguntar_llm(
            pergunta,
            contexto_produtos=contexto,
            idioma=idioma,
            historico=memoria["historico_conversas"][:-1],
            todos_produtos=list(memoria["produtos_mencionados"].values()),
        )
    memoria["historico_conversas"].append({"role": "assistant", "content": resposta})
    return {"resposta": resposta, "resultados": produtos, "acao": "MOSTRAR_PRODUTOS"}



def is_pedido_mais_opcoes(texto_baixo):
    texto = normalizar_texto(texto_baixo)
    termos_mais = ["mais opcao", "mais opcoes", "outra opcao", "outras opcoes", "outros", "outras", "tem mais", "mostra mais", "mostre mais", "ver mais"]
    return any(t in texto for t in termos_mais)


async def pipeline_processar(pergunta, idioma="pt"):
    print(f"\n--- Nova Requisicao: {pergunta} --- Idioma: {idioma}")
    
    # Garante a inicialização do histórico e variáveis
    if "historico_conversas" not in memoria:
        memoria["historico_conversas"] = []
    if "produtos_mencionados" not in memoria:
        memoria["produtos_mencionados"] = {}
    if "produtos_escolhidos" not in memoria:
        memoria["produtos_escolhidos"] = []
    if "tentativas_silencio" not in memoria:
        memoria["tentativas_silencio"] = 0

    if not pergunta or not pergunta.strip():
        memoria["tentativas_silencio"] += 1
        if memoria["tentativas_silencio"] == 1:
            resposta_texto = (
                "Olá, tem alguém aí?"
                if idioma == "pt"
                else "Hello, is anyone there?"
            )
            memoria["historico_conversas"].append({"role": "assistant", "content": resposta_texto})
            return {"resposta": resposta_texto, "resultados": [], "acao": "NENHUM"}
        else:
            resposta_texto = texto_encerramento(idioma)
            limpar_memoria()
            return {"resposta": resposta_texto, "resultados": [], "acao": "ENCERRAR"}

    # Se o usuário falou algo, reseta as tentativas de silêncio
    memoria["tentativas_silencio"] = 0

    texto_baixo = pergunta.lower()

    # Detecta gênero na pergunta atual e armazena na memória
    tokens_pergunta = normalizar_texto(texto_baixo).split()
    genero_detectado = detectar_genero(tokens_pergunta)
    if "genero" not in memoria:
        memoria["genero"] = None
    if genero_detectado:
        if memoria.get("genero") and memoria["genero"] != genero_detectado:
            memoria["ultimos_produtos"] = []
            memoria["produtos_mencionados"] = {}
            memoria["produtos_escolhidos"] = []
            memoria["produtos_pendentes_confirmacao"] = []
            memoria["tipo_ativo"] = None
        memoria["genero"] = genero_detectado
        print(f"[Memoria] Genero atualizado para: {genero_detectado}")
    
    memoria["historico_conversas"].append({"role": "user", "content": pergunta})
    
    produtos_memoria = memoria.get("ultimos_produtos", [])
    # Se a memoria de ultimos produtos estiver vazia mas temos produtos mencionados na sessao,
    # usamos os produtos mencionados como fallback para o contexto da conversa.
    if not produtos_memoria and memoria.get("produtos_mencionados"):
        produtos_memoria = list(memoria["produtos_mencionados"].values())
        
    produtos_pendentes = memoria.get("produtos_pendentes_confirmacao", [])
    ia_ofereceu_mapa = ia_ofereceu_mapa_no_historico()
    confirmacao_mapa_pendente = (
        bool(produtos_memoria)
        and ia_ofereceu_mapa
        and is_confirmacao_positiva(texto_baixo)
    )

    if is_encerramento(texto_baixo):
        resposta_texto = texto_encerramento(idioma)
        limpar_memoria()
        return {"resposta": resposta_texto, "resultados": [], "acao": "ENCERRAR"}

    # Verifica se o usuário está pedindo mais opções / variação do tipo ativo
    if is_pedido_mais_opcoes(texto_baixo) and memoria.get("tipo_ativo"):
        tipo_ativo = memoria["tipo_ativo"]
        genero = memoria.get("genero")
        
        # Busca produtos do mesmo tipo
        todos = listar_todos_produtos_formatados()
        candidatos = [p for p in todos if token_match(texto_produto(p), tipo_ativo)]
        
        # Exclui os que já foram mostrados recentemente
        ids_mostrados = {p["id"] for p in memoria.get("ultimos_produtos", [])}
        novos_candidatos = [p for p in candidatos if p["id"] not in ids_mostrados]
        
        if novos_candidatos:
            disponiveis = novos_candidatos[:3]
            memoria["ultimos_produtos"] = disponiveis
            memoria["assunto_ativo"] = "produto"
            memoria["produtos_pendentes_confirmacao"] = disponiveis
            for p in disponiveis:
                memoria["produtos_mencionados"][p["id"]] = p
                
            resposta = montar_resposta_busca_natural(disponiveis, idioma=idioma)
            memoria["historico_conversas"].append({"role": "assistant", "content": resposta})
            return {"resposta": resposta, "resultados": disponiveis, "acao": "MOSTRAR_PRODUTOS"}
        else:
            if idioma == "pt":
                resposta = f"Ja te mostrei todas as opcoes de {tipo_ativo} disponiveis no momento. Gostaria de ver outros tipos de roupas?"
            else:
                resposta = f"I have already shown you all available options for {tipo_ativo}. Would you like to see other types of clothing?"
            
            sugestoes = listar_amostra_catalogo(3)
            memoria["historico_conversas"].append({"role": "assistant", "content": resposta})
            return {"resposta": resposta, "resultados": sugestoes, "acao": "MOSTRAR_PRODUTOS"}

    # Verifica se o usuário está pedindo para ir ao provador
    if is_pedido_provador(texto_baixo):
        todos_mencionados = list(memoria.get("produtos_mencionados", {}).values())
        base_produtos = todos_mencionados if todos_mencionados else produtos_memoria
        
        # Cria lista de destinos: produtos + provador + caixa
        destinos = [p for p in base_produtos]
        destinos.append({
            "id": "provador",
            "nome": "Provadores",
            "corredor": "8",
            "setor": "Provadores"
        })
        destinos.append({
            "id": "caixa",
            "nome": "Caixas",
            "corredor": "9",
            "setor": "Caixas"
        })
        
        resposta_texto = (
            "Os produtos estão aqui e o provador está aqui, se gostar só ir no caixa."
            if idioma == "pt"
            else "The products are here and the fitting room is here, if you like them just go to the checkout."
        )
        memoria["historico_conversas"].append({"role": "assistant", "content": resposta_texto})
        return {
            "resposta": resposta_texto,
            "resultados": destinos,
            "acao": "ABRIR_ROTAS"
        }

    # Verifica se o usuário está pedindo para efetuar a compra / ir ao caixa
    if is_confirmacao_compra(texto_baixo):
        todos_mencionados = list(memoria.get("produtos_mencionados", {}).values())
        base_produtos = todos_mencionados if todos_mencionados else produtos_memoria
        produtos_rota = produtos_por_secao(base_produtos)
        memoria["produtos_escolhidos"] = produtos_rota
        destinos = produtos_rota + [destino_caixa()]
        resposta_texto = (
            "Perfeito. Vou mostrar a rota dos produtos que voce gostou e, no final, o caminho ate o caixa."
            if idioma == "pt"
            else "Perfect. I will show the route for the items you liked and then the way to checkout."
        )
        memoria["historico_conversas"].append({"role": "assistant", "content": resposta_texto})
        return {
            "resposta": resposta_texto,
            "resultados": destinos,
            "acao": "ABRIR_ROTAS"
        }

    if is_pedido_caixa(texto_baixo):
        destino_caixa_rota = [destino_caixa()]
        resposta_texto = (
            "Você pode efetuar a compra nos caixas. Mostrando o caminho no mapa."
            if idioma == "pt"
            else "You can complete your purchase at the registers. Showing the route on the map."
        )
        memoria["historico_conversas"].append({"role": "assistant", "content": resposta_texto})
        return {
            "resposta": resposta_texto,
            "resultados": destino_caixa_rota,
            "acao": "ABRIR_MAPA"
        }

    # Verifica se o usuário está pedindo um atendente humano
    if is_pedido_atendente(texto_baixo):
        produtos_alerta = (
            memoria.get("produtos_escolhidos")
            or memoria.get("ultimos_produtos")
            or list(memoria["produtos_mencionados"].values())[:1]
        )
        resposta_texto = (
            "Claro! Estou chamando um atendente para te ajudar. Em instantes alguém virá até você."
            if idioma == "pt"
            else "Of course! I'm calling an attendant to help you. Someone will be with you shortly."
        )
        resposta_texto = (
            "Claro! Estou chamando um atendente para te ajudar. Em instantes alguem vira ate voce. Muito obrigado e boas compras!"
            if idioma == "pt"
            else "Of course! I'm calling an attendant to help you. Someone will be with you shortly. Thank you, and enjoy your shopping!"
        )
        memoria["historico_conversas"].append({"role": "assistant", "content": resposta_texto})
        return {"resposta": resposta_texto, "resultados": produtos_alerta, "acao": "CHAMAR_ATENDENTE"}

    if is_pergunta_pagamento(texto_baixo):
        resposta_texto = (
            "Sobre pagamento, eu consigo te ajudar melhor com os produtos e a localização deles. "
            "Formas como boleto, Pix ou cartão precisam ser confirmadas no caixa da loja."
            if idioma == "pt"
            else "For payment, I can best help with products and their location. Methods like bank slip, Pix, or card should be confirmed at checkout."
        )
        memoria["historico_conversas"].append({"role": "assistant", "content": resposta_texto})
        return {"resposta": resposta_texto, "resultados": [], "acao": "NENHUM"}

    if confirmacao_mapa_pendente:
        memoria["produtos_pendentes_confirmacao"] = []
        todos_mencionados = list(memoria["produtos_mencionados"].values())
        pool_mapa = todos_mencionados if todos_mencionados else produtos_memoria
        produtos_rota = produtos_por_secao(pool_mapa)
        if len(produtos_rota) > 1:
            resposta_texto = (
                f"Otimo! Mostrando {len(produtos_rota)} rotas no mapa."
                if idioma == "pt"
                else f"Great! Showing {len(produtos_rota)} routes on the map."
            )
            memoria["historico_conversas"].append({"role": "assistant", "content": resposta_texto})
            return {"resposta": resposta_texto, "resultados": produtos_rota, "acao": "ABRIR_ROTAS"}

        produto_mapa = produtos_rota[0] if produtos_rota else produtos_memoria[0]
        resposta_texto = (
            "Otimo! Mostrando o caminho no mapa."
            if idioma == "pt"
            else "Great! Showing the route on the map."
        )
        memoria["historico_conversas"].append({"role": "assistant", "content": resposta_texto})
        return {"resposta": resposta_texto, "resultados": [produto_mapa], "acao": "ABRIR_MAPA"}

    if produtos_pendentes and is_confirmacao_lista(texto_baixo):
        if is_pedido_mapa(texto_baixo):
            memoria["produtos_pendentes_confirmacao"] = []
        else:
            memoria["produtos_pendentes_confirmacao"] = []
            if idioma == "pt":
                resposta_texto = (
                    "Perfeito, já adicionei essa opção à sua lista. Gostaria de ver o mapa para saber como chegar até ela, ou podemos encerrar o atendimento?"
                    if len(produtos_pendentes) == 1
                    else "Perfeito, já adicionei essas opções à sua lista. Gostaria de ver o mapa para saber como chegar até elas, ou podemos encerrar o atendimento?"
                )
            else:
                resposta_texto = (
                    "Perfect! I have added this option to your list. Would you like to see the map to locate it, or can we end the session?"
                    if len(produtos_pendentes) == 1
                    else "Perfect! I have added these options to your list. Would you like to see the map to locate them, or can we end the session?"
                )
            memoria["historico_conversas"].append({"role": "assistant", "content": resposta_texto})
            return {
                "resposta": resposta_texto,
                "resultados": produtos_pendentes,
                "acao": "MOSTRAR_PRODUTOS",
                "auto_add_lista": True,
            }

    if produtos_pendentes and is_negacao_curta(texto_baixo):
        memoria["produtos_pendentes_confirmacao"] = []
        resposta_texto = (
            "Tudo bem. Se quiser, eu procuro outras opcoes para voce."
            if idioma == "pt"
            else "No problem. I can show you other similar options if you want."
        )
        memoria["historico_conversas"].append({"role": "assistant", "content": resposta_texto})
        return {"resposta": resposta_texto, "resultados": [], "acao": "NENHUM"}

    if is_pedido_resumo_rotas(texto_baixo) and memoria["produtos_mencionados"]:
        produtos_rota = produtos_por_secao(memoria["produtos_mencionados"].values())
        if produtos_rota:
            memoria["produtos_pendentes_confirmacao"] = []
            if idioma == "pt":
                if len(produtos_rota) == 1:
                    resposta_texto = "Claro! Aqui está a seção do produto que conversamos."
                else:
                    resposta_texto = f"Claro! Aqui estão as {len(produtos_rota)} seções dos produtos que conversamos."
            else:
                if len(produtos_rota) == 1:
                    resposta_texto = "Sure! Here is the section for the product we discussed."
                else:
                    resposta_texto = f"Sure! Here are the {len(produtos_rota)} sections for the products we discussed."
            memoria["historico_conversas"].append({"role": "assistant", "content": resposta_texto})
            return {"resposta": resposta_texto, "resultados": produtos_rota, "acao": "ABRIR_ROTAS"}

    # Se o usuário pediu explicitamente um mapa e citou um produto na mesma frase
    if is_pedido_mapa(texto_baixo):
        # 1. Primeiro tenta ver se os produtos já estão na memória de mencionados na conversa
        produtos_do_mapa = []
        mencionados = list(memoria.get("produtos_mencionados", {}).values())
        if mencionados:
            # Filtra os mencionados que combinam com os termos citados na pergunta
            tokens_busca = [
                t for t in normalizar_texto(texto_baixo).replace(",", " ").replace("?", " ").split()
                if len(t) > 2 and t not in {"mapa", "caminho", "onde", "fica", "como", "chegar", "mostrar", "mostra", "ver", "rotas", "rota"}
            ]
            # Usa selecionar_produtos_para_mapa para extrair do pool de mencionados
            produtos_do_mapa = selecionar_produtos_para_mapa(texto_baixo, mencionados)
            # Confirma se realmente houve algum match de token na busca de mapa
            has_match = False
            for p in produtos_do_mapa:
                texto_p = texto_produto(p)
                if any(token_match(texto_p, token) for token in tokens_busca):
                    has_match = True
                    break
            if not has_match:
                produtos_do_mapa = []

        # 2. Se não encontrou correspondência na memória, faz a busca segmentada no banco de dados
        if not produtos_do_mapa:
            palavras_busca = extrair_palavras_busca(texto_baixo)
            termos_excluir = {"mapa", "localizacao", "caminho", "onde", "fica", "ficar", "como", "chegar", "ir", "para", "sessao", "corredor", "ver", "mostra", "mostrar", "me", "rotas", "rota"}
            palavras_filtradas = [p for p in palavras_busca if p not in termos_excluir]
            
            # Usar buscar_produtos_por_segmentos para respeitar os múltiplos produtos (ex: "camisa e calça")
            busca_seg = buscar_produtos_por_segmentos(texto_baixo, palavras_validas=palavras_filtradas) if palavras_filtradas else None
            resultados = busca_seg["produtos"] if (busca_seg and busca_seg.get("produtos")) else []
            if resultados:
                disponiveis = [p for p in resultados if not p.get("_esgotado")]
                produtos_do_mapa = disponiveis[:3]

        if produtos_do_mapa:
            memoria["ultimos_produtos"] = produtos_do_mapa
            memoria["assunto_ativo"] = "produto"
            memoria["produtos_pendentes_confirmacao"] = []
            for p in produtos_do_mapa:
                memoria["produtos_mencionados"][p["id"]] = p
            
            produtos_rota = produtos_por_secao(produtos_do_mapa)
            resposta = montar_resposta_mapa(produtos_do_mapa, idioma) # Mostra a contagem real de produtos no texto
            memoria["historico_conversas"].append({"role": "assistant", "content": resposta})
            
            acao_mapa = "ABRIR_ROTAS" if len(produtos_rota) > 1 else "ABRIR_MAPA"
            return {"resposta": resposta, "resultados": produtos_rota, "acao": acao_mapa}

    if is_pedido_catalogo_por_genero(texto_baixo):
        return await responder_catalogo_por_genero(pergunta, idioma)

    if is_pedido_catalogo_geral(texto_baixo):
        return await responder_catalogo_geral(pergunta, idioma)

    if is_pedido_por_occasiao(texto_baixo):
        return await responder_por_occasiao(pergunta, idioma)

    analise = await classificar_intencao(pergunta, idioma)
    intencao = analise.get("intencao", "OUTROS")
    palavras = analise.get("palavras_chave", [])

    if intencao == "ENCERRAR":
        resposta_texto = texto_encerramento(idioma)
        limpar_memoria()
        return {"resposta": resposta_texto, "resultados": [], "acao": "ENCERRAR"}

    pedido_mapa_explicito = is_pedido_mapa(texto_baixo)
    intencao_mapa_valida = (
        intencao == "IR_PARA_MAPA"
        and (pedido_mapa_explicito or not is_confirmacao_positiva(texto_baixo))
    )
    if intencao == "IR_PARA_MAPA" and not intencao_mapa_valida:
        intencao = "OUTROS"

    if produtos_memoria and (intencao_mapa_valida or pedido_mapa_explicito):
        memoria["produtos_pendentes_confirmacao"] = []
        # Usa todos os produtos já mencionados na sessão, não só os últimos
        todos_mencionados = list(memoria["produtos_mencionados"].values())
        pool_mapa = todos_mencionados if (is_pedido_resumo_rotas(texto_baixo) or menciona_todos_os_produtos(texto_baixo)) else produtos_memoria
        produtos_mapa = selecionar_produtos_para_mapa(texto_baixo, produtos_memoria)
        
        # Verifica se o usuário citou algum dos produtos especificamente
        citou_produto_especifico = False
        if len(produtos_memoria) > 1:
            palavras_req = [normalizar_texto(w.strip(".,?!")) for w in texto_baixo.split()]
            for prod in produtos_memoria:
                nome_partes = [normalizar_texto(p) for p in prod["nome"].lower().split()]
                if any(p in palavras_req for p in nome_partes):
                    citou_produto_especifico = True
                    break

        # Se a frase é genérica/afirmativa, mostra todas as seções da sessão
        if (
            is_confirmacao_positiva(texto_baixo)
            or is_pedido_resumo_rotas(texto_baixo)
            or menciona_todos_os_produtos(texto_baixo)
            or (len(produtos_memoria) > 1 and not citou_produto_especifico)
        ):
            produtos_mapa = pool_mapa
        produtos_rota = produtos_por_secao(produtos_mapa)
        if len(produtos_rota) > 1:
            resposta_texto = montar_resposta_mapa(produtos_rota, idioma)
            memoria["historico_conversas"].append({"role": "assistant", "content": resposta_texto})
            return {"resposta": resposta_texto, "resultados": produtos_rota, "acao": "ABRIR_ROTAS"}

        produto_mapa = produtos_rota[0] if produtos_rota else produtos_memoria[0]
        resposta_texto = montar_resposta_mapa([produto_mapa], idioma)
        memoria["historico_conversas"].append({"role": "assistant", "content": resposta_texto})
        return {"resposta": resposta_texto, "resultados": [produto_mapa], "acao": "ABRIR_MAPA"}

    if intencao == "SOBRE_PRODUTO" and not produtos_memoria:
        intencao = "NOVA_BUSCA"
        palavras = extrair_palavras_busca(texto_baixo)

    print(f"Intencao: {intencao} | Palavras: {palavras}")

    if intencao == "NOVA_BUSCA":
        # Context inheritance / Query expansion
        tem_tipo = any(p.lower() in TIPOS_CONHECIDOS or (len(p) > 3 and p.lower().endswith("s") and p.lower()[:-1] in TIPOS_CONHECIDOS) for p in palavras)
        if not tem_tipo and memoria.get("tipo_ativo"):
            tipo_herdado = memoria["tipo_ativo"]
            palavras.append(tipo_herdado)
            texto_baixo = f"{texto_baixo} {tipo_herdado}"
            pergunta = f"{pergunta} {tipo_herdado}"
            print(f"[Contexto] Herdando tipo ativo: {tipo_herdado}. Nova pergunta: {pergunta}")

        busca_segmentada = buscar_produtos_por_segmentos(texto_baixo, palavras_validas=palavras)
        if busca_segmentada and busca_segmentada.get("produtos"):
            disponiveis = busca_segmentada["produtos"][:3]
            memoria["ultimos_produtos"] = disponiveis
            memoria["assunto_ativo"] = "produto"
            memoria["produtos_pendentes_confirmacao"] = disponiveis
            for p in disponiveis:
                memoria["produtos_mencionados"][p["id"]] = p
            if disponiveis:
                tipo_val = disponiveis[0].get("tipo")
                memoria["tipo_ativo"] = normalizar_texto(tipo_val) if tipo_val else None

            resposta = montar_resposta_busca_natural(disponiveis, busca_segmentada.get("faltas", []), idioma)
            memoria["historico_conversas"].append({"role": "assistant", "content": resposta})
            return {"resposta": resposta, "resultados": disponiveis, "acao": "MOSTRAR_PRODUTOS"}
        if busca_segmentada and busca_segmentada.get("faltas"):
            memoria["ultimos_produtos"] = []
            memoria["assunto_ativo"] = None
            memoria["produtos_pendentes_confirmacao"] = []
            resposta = montar_resposta_busca_natural([], busca_segmentada.get("faltas", []), idioma)
            memoria["historico_conversas"].append({"role": "assistant", "content": resposta})
            return {"resposta": resposta, "resultados": [], "acao": "NENHUM"}

        resultados = buscar_produtos_sql(palavras)
        if resultados:
            # Verifica se são produtos esgotados
            esgotados = [p for p in resultados if p.get("_esgotado")]
            disponiveis = [p for p in resultados if not p.get("_esgotado")]

            if esgotados and not disponiveis:
                # Produto existe mas está esgotado
                nomes = ", ".join(p["nome"] for p in esgotados[:2])
                contexto = (
                    f"ATENÇÃO: O(s) produto(s) '{nomes}' exist(e/m) no catálogo MAS ESTÁ(ÃO) ESGOTADO(S) (estoque = 0). "
                    f"Informe ao usuário de forma gentil que o produto está esgotado no momento e ofereça ajuda para encontrar outra opção."
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
                return {"resposta": resposta, "resultados": [], "acao": "NENHUM"}

            # Produtos com estoque disponível — fluxo normal
            memoria["ultimos_produtos"] = disponiveis[:3]
            memoria["assunto_ativo"] = "produto"
            memoria["produtos_pendentes_confirmacao"] = disponiveis[:3]
            for p in disponiveis[:3]:
                memoria["produtos_mencionados"][p["id"]] = p
            if disponiveis:
                tipo_val = disponiveis[0].get("tipo")
                memoria["tipo_ativo"] = normalizar_texto(tipo_val) if tipo_val else None

            contexto = "Produtos encontrados no banco de dados:\n" + "\n---\n".join(
                [formatar_produto_para_contexto(p) for p in disponiveis[:3]]
            )
            todos_prods = list(memoria["produtos_mencionados"].values())
            if len(disponiveis[:3]) > 1:
                resposta = montar_resposta_busca_natural(disponiveis[:3], idioma=idioma)
            else:
                resposta = await perguntar_llm(
                    pergunta,
                    contexto_produtos=contexto,
                    idioma=idioma,
                    historico=memoria["historico_conversas"][:-1],
                    todos_produtos=todos_prods
                )
            memoria["historico_conversas"].append({"role": "assistant", "content": resposta})
            return {"resposta": resposta, "resultados": disponiveis[:3], "acao": "MOSTRAR_PRODUTOS"}


        memoria["ultimos_produtos"] = []
        memoria["assunto_ativo"] = None
        memoria["produtos_pendentes_confirmacao"] = []
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
        palavras_pergunta = [w.strip(".,?!") for w in texto_baixo.split()]
        palavras_pergunta_norm = [normalizar_texto(p) for p in palavras_pergunta]
        
        # 1. Busca primeiro nos produtos já mencionados na sessão
        for produto in memoria.get("produtos_mencionados", {}).values():
            nome_partes = [normalizar_texto(p) for p in produto["nome"].lower().split()]
            if any(parte in palavras_pergunta_norm for parte in nome_partes):
                if produto["id"] not in [p["id"] for p in produtos_relevantes]:
                    produtos_relevantes.append(produto)

        # 2. Se não achou nos mencionados, busca no banco pelas palavras-chave da intenção
        if not produtos_relevantes:
            palavras_busca = palavras if palavras else extrair_palavras_busca(texto_baixo)
            resultados_db = buscar_produtos_sql(palavras_busca) if palavras_busca else []
            if resultados_db:
                disponiveis = [p for p in resultados_db if not p.get("_esgotado")]
                if disponiveis:
                    memoria["ultimos_produtos"] = disponiveis[:3]
                    memoria["assunto_ativo"] = "produto"
                    memoria["produtos_pendentes_confirmacao"] = disponiveis[:3]
                    for p in disponiveis[:3]:
                        memoria["produtos_mencionados"][p["id"]] = p
                    produtos_relevantes = disponiveis[:3]
        else:
            # Atualiza os últimos produtos e pendentes com a seleção relevante filtrada da pergunta
            memoria["ultimos_produtos"] = produtos_relevantes
            memoria["produtos_pendentes_confirmacao"] = produtos_relevantes

        final_context = produtos_relevantes if produtos_relevantes else produtos_memoria
        return await responder_sobre_produtos(pergunta, final_context, idioma)

    if intencao_mapa_valida:
        if produtos_memoria:
            todos_mencionados = list(memoria["produtos_mencionados"].values())
            pool_mapa = todos_mencionados if (is_pedido_resumo_rotas(texto_baixo) or menciona_todos_os_produtos(texto_baixo)) else produtos_memoria
            produtos_mapa = selecionar_produtos_para_mapa(texto_baixo, produtos_memoria)
            
            # Verifica se o usuário citou algum dos produtos especificamente
            citou_produto_especifico = False
            if len(produtos_memoria) > 1:
                palavras_req = [normalizar_texto(w.strip(".,?!")) for w in texto_baixo.split()]
                for prod in produtos_memoria:
                    nome_partes = [normalizar_texto(p) for p in prod["nome"].lower().split()]
                    if any(p in palavras_req for p in nome_partes):
                        citou_produto_especifico = True
                        break

            if (
                is_confirmacao_positiva(texto_baixo)
                or is_pedido_resumo_rotas(texto_baixo)
                or menciona_todos_os_produtos(texto_baixo)
                or (len(produtos_memoria) > 1 and not citou_produto_especifico)
            ):
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

