import sqlite3
import os
from services.llm_service import classificar_intencao, perguntar_llm

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "..", "database", "produtos.db")

memoria = {
    "ultimos_produtos": [],
}

def conectar_bd():
    return sqlite3.connect(DB_PATH)


def formatar_produto(produto):
    return {
        "id": produto[0],
        "nome": produto[1],
        "categoria": produto[2],
        "tipo": produto[3],
        "cor": produto[4],
        "tamanho": produto[5],
        "marca": produto[6],
        "preco": produto[7],
        "estoque": produto[8],
        "setor": produto[9],
        "corredor": produto[10],
        "prateleira": produto[11],
        "descricao": produto[12]
    }

def formatar_produto_para_contexto(p):
    return (
        f"Nome: {p['nome']} | Preço: R${p['preco']:.2f} | "
        f"Estoque: {p['estoque']} | Descrição: {p['descricao']} | "
        f"Cor: {p['cor']} | Tamanho: {p['tamanho']} | Marca: {p['marca']}"
    )

def buscar_produtos_sql(palavras_chave):
    if not palavras_chave:
        return []

    conn = conectar_bd()
    cursor = conn.cursor()
    colunas = ["nome", "categoria", "tipo", "cor", "marca", "descricao"]

    # 1. Tenta AND (todos os termos presentes no produto)
    clausulas_and = []
    parametros_and = []
    for palavra in palavras_chave:
        or_interno = [f"{col} LIKE ?" for col in colunas]
        parametros_and += [f"%{palavra}%" for _ in colunas]
        clausulas_and.append("(" + " OR ".join(or_interno) + ")")

    query_and = f"SELECT * FROM produtos WHERE {' AND '.join(clausulas_and)}"
    cursor.execute(query_and, parametros_and)
    produtos = cursor.fetchall()

    # 2. Fallback OR com ranqueamento por relevância
    if not produtos:
        contagem = {}
        for palavra in palavras_chave:
            or_interno = [f"{col} LIKE ?" for col in colunas]
            params = [f"%{palavra}%" for _ in colunas]
            query = f"SELECT * FROM produtos WHERE {' OR '.join(or_interno)}"
            cursor.execute(query, params)
            for p in cursor.fetchall():
                pid = p[0]
                if pid not in contagem:
                    contagem[pid] = {"count": 0, "data": p}
                contagem[pid]["count"] += 1

        sorted_ids = sorted(contagem.keys(), key=lambda x: contagem[x]["count"], reverse=True)
        produtos = [contagem[i]["data"] for i in sorted_ids]

    conn.close()
    return [formatar_produto(p) for p in produtos]


async def pipeline_processar(pergunta, idioma="pt"):
    print(f"\n--- Nova Requisição: {pergunta} --- Idioma: {idioma}")
    analise = await classificar_intencao(pergunta, idioma)
    intencao = analise.get("intencao", "OUTROS")
    palavras = analise.get("palavras_chave", [])

    texto_baixo = pergunta.lower()

    # --- Correção de Intenção ---
    # Se veio como SOBRE_PRODUTO mas não há memória, force nova busca
    if intencao == "SOBRE_PRODUTO" and not memoria["ultimos_produtos"]:
        print("SOBRE_PRODUTO sem memória → forçando NOVA_BUSCA")
        intencao = "NOVA_BUSCA"
        # Extrai palavras da pergunta como palavras-chave
        stopwords = {"eu", "quero", "saber", "mais", "sobre", "a", "o", "as", "os", "de", "da", "do", "tem", "há", "me", "fale"}
        palavras = [w for w in texto_baixo.split() if len(w) > 2 and w not in stopwords]

    print(f"Intenção: {intencao} | Palavras: {palavras}")

    # ========================
    # ENCERRAR
    # ========================
    despedidas = ["tchau", "obrigado", "obrigada", "valeu", "encerrar", "até logo", "bye", "thanks", "falou"]
    is_despedida = any(w in texto_baixo.split() for w in despedidas) and len(texto_baixo.split()) <= 4
    
    if intencao == "ENCERRAR" or is_despedida:
        msg = "Muito obrigado e volte sempre!" if idioma == "pt" else "Thank you very much and come back soon!"
        return {"resposta": msg, "resultados": [], "acao": "ENCERRAR"}

    # ========================
    # NOVA_BUSCA
    # ========================
    if intencao == "NOVA_BUSCA":
        resultados = buscar_produtos_sql(palavras)
        if resultados:
            memoria["ultimos_produtos"] = resultados[:3]
            contexto = "Produtos encontrados no banco de dados:\n" + "\n---\n".join(
                [formatar_produto_para_contexto(p) for p in resultados[:3]]
            )
            resposta = await perguntar_llm(pergunta, contexto, idioma)
            return {"resposta": resposta, "resultados": resultados[:3], "acao": "MOSTRAR_PRODUTOS"}
        else:
            memoria["ultimos_produtos"] = []
            resposta_base = "Nenhum produto encontrado no banco de dados com esses termos. Informe ao usuário."
            resposta = await perguntar_llm(pergunta, resposta_base, idioma)
            return {"resposta": resposta, "resultados": [], "acao": "NENHUM"}

    # ========================
    # SOBRE_PRODUTO
    # ========================
    elif intencao == "SOBRE_PRODUTO":
        produtos_atuais = memoria["ultimos_produtos"]

        # Filtro inteligente: verifica se o usuário citou um produto específico da memória
        produtos_relevantes = []
        palavras_pergunta = texto_baixo.split()
        for p in produtos_atuais:
            nome_partes = p['nome'].lower().split()
            if any(parte in palavras_pergunta for parte in nome_partes):
                produtos_relevantes.append(p)

        final_context = produtos_relevantes if produtos_relevantes else produtos_atuais

        contexto = "O usuário está perguntando sobre estes produtos:\n" + "\n---\n".join(
            [formatar_produto_para_contexto(p) for p in final_context]
        )
        resposta = await perguntar_llm(pergunta, contexto, idioma)
        return {"resposta": resposta, "resultados": final_context, "acao": "MOSTRAR_PRODUTOS"}

    # ========================
    # IR_PARA_MAPA
    # ========================
    elif intencao == "IR_PARA_MAPA":
        produtos_atuais = memoria.get("ultimos_produtos", [])
        if produtos_atuais:
            # We assume the user wants to go to the first product in memory
            resposta_texto = "Ótimo! Vou te mostrar o caminho no mapa agora." if idioma == "pt" else "Great! I'll show you the way on the map now."
            return {"resposta": resposta_texto, "resultados": [produtos_atuais[0]], "acao": "ABRIR_MAPA"}
        else:
            resposta_texto = "Qual produto você gostaria de ver no mapa?" if idioma == "pt" else "Which product would you like to see on the map?"
            return {"resposta": resposta_texto, "resultados": [], "acao": "NENHUM"}

    # ========================
    # OUTROS
    # ========================
    else:
        contexto = "Conversa casual ou dúvida geral. Responda naturalmente como assistente de uma loja de roupas."
        resposta = await perguntar_llm(pergunta, contexto, idioma)
        return {"resposta": resposta, "resultados": [], "acao": "NENHUM"}