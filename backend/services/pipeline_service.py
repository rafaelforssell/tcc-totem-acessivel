import sqlite3
import os
from services.llm_service import classificar_intencao, perguntar_llm

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "..", "database", "produtos.db")

memoria = {
    "ultimo_produto": None,
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
        f"Setor: {p['setor']} | Corredor: {p['corredor']} | Prateleira: {p['prateleira']} | "
        f"Estoque: {p['estoque']} | Descrição: {p['descricao']} | "
        f"Cor: {p['cor']} | Tamanho: {p['tamanho']} | Marca: {p['marca']}"
    )

def buscar_produtos_sql(palavras_chave):
    if not palavras_chave:
        return []
        
    conn = conectar_bd()
    cursor = conn.cursor()
    
    colunas = ["nome", "categoria", "tipo", "cor", "marca", "descricao"]
    
    # 1. Tenta AND (exige que todas as palavras estejam em alguma coluna do produto)
    clausulas_and = []
    parametros_and = []
    
    for palavra in palavras_chave:
        clausula_or_interna = []
        for col in colunas:
            clausula_or_interna.append(f"{col} LIKE ?")
            parametros_and.append(f"%{palavra}%")
        
        clausulas_and.append("(" + " OR ".join(clausula_or_interna) + ")")
        
    query_and = f"SELECT * FROM produtos WHERE {' AND '.join(clausulas_and)}"
    
    cursor.execute(query_and, parametros_and)
    produtos = cursor.fetchall()
    
    # 2. Se não achou nada, tenta OR (relaxa a busca, basta ter uma das palavras)
    if not produtos:
        clausulas_or = []
        parametros_or = []
        for palavra in palavras_chave:
            for col in colunas:
                clausulas_or.append(f"{col} LIKE ?")
                parametros_or.append(f"%{palavra}%")
                
        query_or = f"SELECT * FROM produtos WHERE {' OR '.join(clausulas_or)}"
        cursor.execute(query_or, parametros_or)
        produtos = cursor.fetchall()

    conn.close()
    
    return [formatar_produto(p) for p in produtos]

async def pipeline_processar(pergunta):
    print("Classificando intenção...")
    analise = await classificar_intencao(pergunta)
    intencao = analise.get("intencao", "OUTROS")
    palavras = analise.get("palavras_chave", [])
    
    print(f"Intenção: {intencao} | Palavras: {palavras}")
    
    if intencao == "NOVA_BUSCA":
        resultados = buscar_produtos_sql(palavras)
        
        if resultados:
            memoria["ultimo_produto"] = resultados[0]
            contexto = "Produtos Encontrados:\n" + "\n".join(
                [formatar_produto_para_contexto(p) for p in resultados[:3]]
            )
            resposta = await perguntar_llm(pergunta, contexto)
            return {"resposta": resposta, "resultados": resultados[:3]}
        else:
            contexto = "Nenhum produto foi encontrado com esses termos no banco de dados."
            resposta = await perguntar_llm(pergunta, contexto)
            return {"resposta": resposta, "resultados": []}

    elif intencao == "SOBRE_PRODUTO":
        produto_atual = memoria["ultimo_produto"]
        
        if produto_atual:
            contexto = "O usuário está perguntando sobre o seguinte produto do contexto anterior:\n"
            contexto += formatar_produto_para_contexto(produto_atual)
            resposta = await perguntar_llm(pergunta, contexto)
            return {"resposta": resposta, "resultados": [produto_atual]}
        else:
            resposta = await perguntar_llm(pergunta, "O usuário perguntou sobre um produto, mas nenhum produto foi buscado anteriormente.")
            return {"resposta": resposta, "resultados": []}
            
    else:
        # OUTROS (Saudações, perguntas aleatórias)
        resposta = await perguntar_llm(pergunta, "O usuário não está buscando um produto. Responda naturalmente e, se fugir do tema, redirecione para o supermercado/loja.")
        return {"resposta": resposta, "resultados": []}