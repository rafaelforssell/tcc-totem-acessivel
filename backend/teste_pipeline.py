import asyncio

from services.pipeline_service import pipeline_processar


async def main():
    cenarios = [
        ("Saudacao e pergunta aleatoria", "Ola, quem descobriu o Brasil?"),
        ("Nova busca", "Eu queria comprar uma camisa dry fit preta"),
        ("Pergunta de contexto", "Onde fica?"),
        ("Pergunta de contexto 2", "E tem estoque disso?"),
    ]

    for titulo, pergunta in cenarios:
        print(f"\n--- {titulo} ---")
        resposta = await pipeline_processar(pergunta)
        print("Resposta:", resposta["resposta"])
        if resposta.get("resultados"):
            print("Produto retornado:", resposta["resultados"][0]["nome"])


if __name__ == "__main__":
    asyncio.run(main())
