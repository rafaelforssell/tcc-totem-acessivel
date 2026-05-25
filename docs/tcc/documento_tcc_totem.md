# UNIVERSIDADE SANTA CECÍLIA
# ENGENHARIA DA COMPUTAÇÃO

**DAVI XAVIER DE LIMA**  
**KAUÃ SANTOS SILVA**  
**RAFAEL LUIZ FORSSELL FERRARA FOMIN**  

---

# TOTEM DE AUTOATENDIMENTO ACESSÍVEL INTEGRADO COM INTELIGÊNCIA ARTIFICIAL CONVERSACIONAL E MAPEAMENTO INDOOR

---

**Santos – SP**  
**2026**

---

### DAVI XAVIER DE LIMA  
### KAUÃ SANTOS SILVA  
### RAFAEL LUIZ FORSSELL FERRARA FOMIN  

**TOTEM DE AUTOATENDIMENTO ACESSÍVEL INTEGRADO COM INTELIGÊNCIA ARTIFICIAL CONVERSACIONAL E MAPEAMENTO INDOOR**

Trabalho de Conclusão de Curso apresentado como exigência parcial para obtenção do título de Bacharel em Engenharia da Computação da Faculdade de Engenharia da Computação da Universidade Santa Cecília, sob a orientação do Professor Me. Sergio Schina de Andrade.

**Santos – SP**  
**2026**

---

## FOLHA DE APROVAÇÃO

**Davi Xavier de Lima**  
**Kauã Santos Silva**  
**Rafael Luiz Forssell Ferrara Fomin**  

**Totem de Autoatendimento Acessível Integrado com Inteligência Artificial Conversacional e Mapeamento Indoor**

Trabalho de Conclusão de Curso apresentado como exigência para obtenção do título de Engenheiro de Computação à Faculdade de Engenharia de Computação da Universidade Santa Cecília – UNISANTA.

Data da aprovação: ____/____/______  
Nota: ____________

**Banca Examinadora:**

___________________________________________  
**Prof. Me. Sergio Schina de Andrade**  
Orientador  

___________________________________________  
**Prof. Examinador 1**  

___________________________________________  
**Prof. Examinador 2**  

---

## RESUMO

O autoatendimento comercial por meio de totens interativos tornou-se padrão em estabelecimentos modernos. Contudo, a imensa maioria dessas soluções carece de recursos adequados de acessibilidade física, visual e cognitiva, segregando indivíduos com deficiência ou dificuldades de interação digital. Este projeto propõe o desenvolvimento de um Totem de Autoatendimento Acessível integrado com inteligência artificial conversacional e mapeamento indoor dinâmico. A solução baseia-se em um fluxo conversacional multimodal e inclusivo, combinando reconhecimento de fala (STT), síntese de voz (TTS) e processamento de linguagem natural (LLN) via modelo Llama 3.3 hospedado na infraestrutura de alta velocidade da Groq. O sistema foi desenvolvido com arquitetura descentralizada: um front-end em HTML5/JavaScript com suporte a alto contraste, controle de pausa ativa de sessão, e um lightbox responsivo com carrossel para ampliação e zoom de imagens de produtos; e um back-end robusto construído com a biblioteca FastAPI em Python, integrado a um banco de dados relacional SQLite contendo inventário e mapeamento de setores. Para assegurar a inteligibilidade, a IA mantém a memória conversacional de longo prazo de turnos e produtos pesquisados na sessão, fornecendo descrições detalhadas antes de sugerir orientações espaciais. Quando requisitado, uma rota indoor dinâmica é traçada de forma nativa e piscante em um mapa SVG acoplado diretamente na tela de chat. A proposta promove inclusão social alinhada à Lei Brasileira de Inclusão (LBI), otimiza o atendimento comercial e mitiga barreiras de navegação física e lógica de forma autônoma e humanizada.

**Palavras-chave**: Acessibilidade; Totem de Autoatendimento; Inteligência Artificial Conversacional; Mapeamento Indoor; Inclusão Digital; LBI.

---

## LISTA DE FIGURAS

* **Figura 1** - Diagrama de Arquitetura do Sistema e Fluxo de Dados
* **Figura 2** - Tela Inicial do Totem (Modo Espera / Start)
* **Figura 3** - Interface de Conversação (Chat) com Balões Multimodais
* **Figura 4** - Botão Dinâmico de Pausa/Retomada e Indicadores de Captura de Voz
* **Figura 5** - Visualização de Produtos com Zoom (Modal Lightbox)
* **Figura 6** - Rota Indoor no Mapa SVG Integrado no Fluxo de Chat
* **Figura 7** - Detalhamento da Estrutura de Tabelas do Banco de Dados SQLite

---

## SUMÁRIO

1. **Introdução**  
   1.1 Acessibilidade Digital e Legislação Vigente (NRs e LBI)  
   1.2 Interface por Voz e Processamento de Áudio (STT e TTS)  
   1.3 Modelos de Linguagem de Larga Escala (LLMs) e API Groq  
   1.4 Mapeamento Indoor e SVG Dinâmico  
   1.5 Bancos de Dados Relacionais Locais (SQLite)  
2. **Objetivo**  
3. **Metodologia**  
4. **Desenvolvimento**  
   4.1 Arquitetura do Sistema e Estrutura de Diretórios  
   4.2 Estruturação da Camada de Dados (SQLite)  
   4.3 Lógica de Controle Conversacional no Back-end (FastAPI)  
   4.3.1 Processamento do Pipeline de Voz e Texto  
   4.3.2 Lógica de Memória Conversacional e Persistência de Turnos  
   4.3.3 Algoritmo de Extração de Palavras-Chave e Stemming Cognitivo  
   4.4 Lógica de Interface e Interação no Front-end  
   4.4.1 Fluxo de Captura de Áudio, Detecção de Silêncio e MediaRecorder  
   4.4.2 Lógica de Pausa Ativa de Sessão e Privacidade  
   4.4.3 Renderização Dinâmica de Rota Indoor sobre SVG no Chat  
   4.4.4 Modal Lightbox para Ampliação e Carrossel de Imagens  
   4.4.5 Suporte a Alto Contraste e Acessibilidade Visual  
5. **Resultados e Testes**  
6. **Conclusão**  
7. **Referências**  

---

## 1. Introdução

A evolução das interfaces de autoatendimento (kiosks) redefiniu a forma como consumidores interagem com lojas físicas, supermercados, aeroportos e instituições públicas. No entanto, o design focado em usuários sem limitações sensoriais ou físicas cria barreiras críticas para pessoas com deficiência visual, auditiva, idosos ou indivíduos com dificuldades de letramento digital. A acessibilidade digital não é apenas um diferencial de mercado, mas uma imposição ética e legal.

### 1.1 Acessibilidade Digital e Legislação Vigente (NRs e LBI)

No cenário brasileiro, a Lei Brasileira de Inclusão da Pessoa com Deficiência (LBI - Lei nº 13.146/2015) assegura o direito à acessibilidade nas comunicações, na informação e nas tecnologias, tanto em canais públicos quanto privados de atendimento. Os totens tradicionais falham em cumprir essas obrigações legais ao exigir navegação física complexa através de telas touch de alta resolução sem feedback tátil ou sonoro adequado. Esse projeto endereça diretamente esse gargalo ao propor uma interface inteiramente operável por voz natural e com facilidades adaptativas de acessibilidade visual.

### 1.2 Interface por Voz e Processamento de Áudio (STT e TTS)

Para eliminar a barreira física das telas, o projeto utiliza processamento de áudio bidirecional:
* **STT (Speech-to-Text)**: A entrada do usuário é capturada via microfone em formato WebM/WAV e transcrevida em texto pelo back-end.
* **TTS (Text-to-Speech)**: As respostas textuais geradas pela Inteligência Artificial são convertidas de volta em áudio humanizado, permitindo que usuários com deficiência visual compreendam integralmente a resposta sem depender da leitura de telas.

### 1.3 Modelos de Linguagem de Larga Escala (LLMs) e API Groq

Os sistemas de conversação tradicionais baseados em árvores rígidas de decisão frequentemente geram frustração no usuário devido à incapacidade de compreender variações na fala. Este trabalho utiliza o modelo de linguagem avançado Llama 3.3 (70 bilhões de parâmetros) integrado via API Groq. O uso do hardware especializado de processadores LPU (Language Processing Units) da Groq garante tempos de inferência inferiores a 1 segundo, patamar essencial para viabilizar conversas fluidas por voz em tempo real.

### 1.4 Mapeamento Indoor e SVG Dinâmico

Uma das maiores dificuldades de clientes em grandes estabelecimentos comerciais é a orientação espacial (navegação indoor). Diferente do ambiente externo, sistemas baseados em GPS não funcionam com precisão dentro de edifícios. A solução adotada consiste na renderização dinâmica de mapas SVG (Scalable Vector Graphics) diretamente na tela. O SVG permite desenhar trajetos matematicamente escaláveis e destacar corredores específicos sem perda de performance ou resolução gráfica.

### 1.5 Bancos de Dados Relacionais Locais (SQLite)

O sistema de inventário é suportado por um banco de dados relacional leve e autocontido SQLite. Isso possibilita consultas estruturadas de alta velocidade com baixo consumo de memória, permitindo extrair dados sobre nome do produto, categoria, tipo, cor, tamanho, marca, preço, estoque disponível e a exata localização física (setor, corredor e prateleira) para alimentar o pipeline de contexto da inteligência artificial.

---

## 2. Objetivo

Desenvolver, implementar e validar um sistema integrado de Totem de Autoatendimento Acessível que permita a qualquer usuário buscar informações sobre produtos por meio de diálogos livres em áudio ou texto, recebendo como resposta dados detalhados dos produtos e rotas dinâmicas desenhadas em tempo real em um mapa SVG inline, assegurando acessibilidade por meio de recursos sonoros, modo de alto contraste, pausa e controle de privacidade de áudio, e memória persistente da conversa.

---

## 3. Metodologia

A construção do sistema seguiu uma abordagem modular com foco em desenvolvimento robusto de ponta a ponta:
1. **Modelagem de Dados**: Estruturação de um banco de dados em SQLite para catalogar o estoque da loja de roupas de demonstração, incluindo campos detalhados de mapeamento físico.
2. **Desenvolvimento do Back-end**: Implementação de uma API assíncrona com FastAPI em Python, estruturando rotas de chat, áudio e reset de memória.
3. **Desenvolvimento do Front-end**: Criação de uma Single Page Application baseada em Vanilla JavaScript e Tailwind CSS com capturador de áudio integrado (MediaRecorder), detetor de silêncio para parada automática, carrossel de imagens com zoom, controle de pausa e renderização SVG.
4. **Integração de IA**: Parametrização do modelo Llama 3.3 via Groq com prompts de sistema estritos, garantindo o sigilo de localizações diretas na primeira resposta e mantendo a integridade histórica dos turnos.
5. **Implantação Continuada (CI/CD)**: Versionamento do código-fonte com Git, hospedagem do banco e back-end em FastAPI no Render com deploys automáticos, e front-end configurado para execução local ou em painéis touch de alta responsividade.

---

## 4. Desenvolvimento

### 4.1 Arquitetura do Sistema e Estrutura de Diretórios

O projeto foi organizado de forma modular, separando responsabilidades de processamento de áudio, IA, banco de dados e interface do usuário:

```text
tcc-totem-acessivel/
├── backend/
│   ├── audios/                 # Diretório temporário de cache de voz
│   ├── routes/
│   │   ├── produtos.py         # Endpoints para gerenciamento do estoque
│   │   └── query.py            # Endpoints de pipeline de texto e áudio
│   ├── services/
│   │   ├── llm_service.py      # Integração com API Groq (NLP e Intents)
│   │   ├── pipeline_service.py # Máquina de estados e memória de sessão
│   │   ├── produtos_service.py # Conexão e queries com o banco de dados
│   │   ├── stt_service.py      # Transcrição de áudio
│   │   └── tts_service.py      # Síntese de voz via Edge-TTS
│   ├── main.py                 # Arquivo inicial de configuração FastAPI
│   └── requirements.txt        # Dependências Python
├── database/
│   ├── produtos.db             # Arquivo do banco relacional SQLite
│   └── create_db.py            # Script de inicialização e seed de dados
└── frontend/
    └── index.html              # Interface do usuário (HTML, CSS e JS)
```

### 4.2 Estruturação da Camada de Dados (SQLite)

O banco de dados SQLite (`produtos.db`) conta com a tabela `produtos` estruturada com os seguintes campos:
- `id` (INTEGER, Primary Key): Identificador exclusivo do item.
- `nome` (TEXT): Nome do produto (ex: "Camisa Dry Fit").
- `categoria` (TEXT): Classificação ampla (ex: "Roupa").
- `tipo` (TEXT): Segmentação (ex: "Treino", "Casual").
- `cor` (TEXT): Cor predominante.
- `tamanho` (TEXT): Grade do produto (PP, P, M, G, GG).
- `marca` (TEXT): Fabricante.
- `preco` (REAL): Valor unitário.
- `estoque` (INTEGER): Quantidade física disponível.
- `setor` (TEXT): Setor da loja física (ex: "Esportivo").
- `corredor` (TEXT): O corredor físico onde o item está localizado (valores de "1" a "5").
- `prateleira` (TEXT): Detalhe da prateleira (ex: "Arara 4").
- `descricao` (TEXT): Descrição textual para alimentar a IA e o painel de detalhes.

### 4.3 Lógica de Controle Conversacional no Back-end (FastAPI)

#### 4.3.1 Processamento do Pipeline de Voz e Texto
O arquivo `backend/routes/query.py` implementa a rota principal `/query-audio`. Quando recebe o arquivo de áudio WebM gravado pelo microfone do Totem, o pipeline executa em três etapas síncronas:
1. **STT (Transcrição)**: O arquivo de áudio temporário é processado e convertido em texto em português brasileiro.
2. **Pipeline NLP**: O texto transcrito é enviado para `pipeline_processar()`.
3. **TTS (Síntese)**: A resposta textual gerada pela IA é enviada para o serviço de áudio Edge-TTS, que gera um arquivo MP3 sob demanda que é retornado em formato de cache e tocado imediatamente no front-end.

#### 4.3.2 Lógica de Memória Conversacional e Persistência de Turnos
O maior diferencial de inteligência e acessibilidade do Totem é o objeto `memoria` controlado no `pipeline_service.py`. A estrutura do objeto é declarada como:

```python
memoria = {
    "ultimos_produtos": [],
    "assunto_ativo": None,
    "historico_conversas": [],
    "produtos_mencionados": {},
}
```

Toda interação executada na sessão adiciona o turno correspondente em `historico_conversas`:
- `{"role": "user", "content": pergunta}`
- `{"role": "assistant", "content": resposta}`

Adicionalmente, qualquer produto encontrado nas buscas do SQLite é armazenado de forma exclusiva (usando seu ID exclusivo como chave) no dicionário `produtos_mencionados`. 

Na chamada de resposta da IA em `llm_service.py`, a lista de `produtos_mencionados` é formatada e injetada diretamente no bloco de sistema do prompt como um contexto persistente. Adicionalmente, as últimas 10 mensagens em `historico_conversas` são anexadas ao payload do chat completion da Groq. Isso garante que o modelo Llama 3.3 saiba de forma exata todos os produtos conversados, permitindo que ao final de um longo diálogo, caso solicitado pelo usuário, uma lista perfeita seja construída com precisão absoluta.

#### 4.3.3 Algoritmo de Extração de Palavras-Chave e Stemming Cognitivo
O totem acessível utiliza a inteligência do Llama 3.3 para classificar intenções e extrair palavras-chave sem a rigidez de expressões regulares. No arquivo `llm_service.py`, a função `classificar_intencao` recebe a pergunta do usuário e classifica-a entre:
- `NOVA_BUSCA`, `SOBRE_PRODUTO`, `IR_PARA_MAPA`, `ENCERRAR`, `OUTROS`

A fim de mitigar problemas de busca causados por plurais, conjugações verbais ou inclusão de números/quantidades (por exemplo, quando o usuário diz *"Eu gostaria de duas camisas para treinar"*), incluímos regras estritas no system prompt da IA de intenções:
1. Extrair substantivos e adjetivos no **singular** e sem variações complexas de gênero.
2. Filtrar e **remover qualquer numeral** ou quantidade (como "dois", "duas", "3").
3. Converter verbos de ação genéricos para substantivos correspondentes (ex: "treinar" vira "treino", "correr" vira "corrida").

Essa normalização de alto nível faz com que a busca relacional no SQLite via `LIKE` funcione perfeitamente, unificando os termos de busca com os dados estruturados do estoque.

### 4.4 Lógica de Interface e Interação no Front-end

#### 4.4.1 Fluxo de Captura de Áudio, Detecção de Silêncio e MediaRecorder
A captura de voz no front-end (`index.html`) inicia a gravação do microfone usando `MediaRecorder` com o stream de áudio capturado pela API de mídia do navegador. Para permitir uma experiência hands-free (essencial para acessibilidade), implementou-se detecção automática de silêncio em JavaScript:
- O áudio é monitorado através de um `AudioContext` com um nó `AnalyserNode`.
- A cada frame visual, a função `detectarSilencio()` calcula o volume Root Mean Square (RMS) do sinal.
- Se o volume cair abaixo do limiar de silêncio (`0.02`) por um período contínuo superior a 1500 milissegundos, o gravador finaliza a captura (`recorder.stop()`) e envia o áudio ao back-end automaticamente, sem exigir cliques do usuário.

#### 4.4.2 Lógica de Pausa Ativa de Sessão e Privacidade
Introduziu-se um botão **Pausar/Retomar** na barra de ferramentas superior do chat.
- Ao clicar em **Pausar**, a variável global `sessaoPausada` é definida como `true`.
- O stream do microfone é interrompido e todas as faixas do microfone são finalizadas (`track.stop()`) por segurança e para garantir a privacidade.
- A função de detecção de silêncio ignora o processamento de quadros.
- O botão se transforma visualmente em um botão de play verde com rótulo "Retomar" e o indicador muda para `PAUSADO`.
- Clicando em **Retomar**, a variável torna-se `false`, uma nova chamada ao microfone (`getUserMedia`) é requisitada de forma segura e o loop conversacional de áudio é restaurado perfeitamente de onde parou.

#### 4.4.3 Renderização Dinâmica de Rota Indoor sobre SVG no Chat
Para evitar que o usuário perca a referência do chat ou navegue para outras telas, o mapa foi embutido diretamente como uma mensagem de chat dinâmica (inline).
- Se a intenção do usuário for categorizada como pedido de mapa (ou ao clicar no botão da tela de detalhes), o front-end chama `createMapCardHtml(productName, aisle)`.
- Essa função gera um bloco de HTML contendo um mapa **SVG** completo.
- O SVG mapeia matematicamente as coordenadas dos corredores 1 a 5 da loja física.
- A partir do corredor retornado, o script destaca a tag `<rect>` correspondente aplicando a cor amarela `#ffd700` e uma borda de destaque.
- A linha de caminho `<path>` é redesenhada de forma precisa ligando a `ENTRADA` ao corredor correspondente por meio de animação pontilhada com a tag `<animate>`.
- O pino de destino `<g id="map-target-pin">` é transladado dinamicamente para o ponto final exato da prateleira.

#### 4.4.4 Modal Lightbox para Ampliação e Carrossel de Imagens
Ao exibir os produtos no chat, as imagens contêm cursores customizados para indicar o zoom.
- Ao clicar especificamente sobre a imagem de um produto em um card de resposta, o front-end dispara `openLightbox(lightboxItems, index)`.
- É aberto o modal `#image-lightbox` em tela cheia com estilo premium: fundo preto semi-transparente e desfoque dinâmico (`backdrop-blur-md`).
- Se a mensagem original contiver múltiplos produtos (por exemplo, resultado de busca de calças), as setas laterais de navegação são exibidas.
- O usuário pode ir para a esquerda ou direita para transitar entre os slides. A cada transição, a nova imagem, o nome do produto, o preço e a contagem ativa ("2 de 3") são atualizados com efeitos suaves de escala (`scale-100`) e transição de opacidade.
- A navegação é acessível via teclado usando as setas do teclado e o botão `Escape`.

#### 4.4.5 Suporte a Alto Contraste e Acessibilidade Visual
Para assegurar a total acessibilidade de usuários com baixa visão ou daltonismo, o totem fornece um botão de alto contraste.
- O clique no botão aplica a classe `.high-contrast` na raiz da página (`<html>`), que força fundos inteiramente pretos e textos com cores puras e alto contraste (branco e amarelo puro).
- O estado é persistido no `localStorage` do navegador para manter o perfil visual do usuário em acessos posteriores.

---

## 5. Resultados e Testes

Os testes sistemáticos de integração do Totem Acessível comprovaram a robustez das soluções implementadas:
1. **Teste de Normalização**: A frase em áudio *"Quero duas camisetas de treino"* foi transcrevida com sucesso. O LLM extraiu apenas `["camisa", "treino"]` como palavras-chave, localizando perfeitamente as opções de **Camisa Dry Fit** no SQLite.
2. **Teste de Conversação e Detalhes**: Em conformidade com o novo fluxo de detalhes, ao buscar a camisa de treino, a IA apresentou primeiro todos os detalhes (tecido dry fit respirável da Nike, cor preta, tamanho GG e valor de R$ 79,90) e finalizou perguntando se o usuário gostou da opção. Ao responder *"sim"*, o mapa com a rota destacando o **Corredor 2** foi renderizado perfeitamente no fluxo da conversa.
3. **Teste de Memória Conversacional**: Buscamos consecutivamente 5 produtos diferentes na mesma sessão. No final, ao perguntarmos *"Quais foram os produtos que conversamos hoje?"*, a IA respondeu com sucesso gerando a listagem ordenada de todos os 5 produtos apresentados anteriormente.
4. **Teste de Terminação e Cancelamento**: Clicar em "Encerrar" no meio do processamento da IA cancelou a reprodução de áudio em tempo de execução, garantindo que o sistema ficasse mudo imediatamente ao retornar à tela inicial.

---

## 6. Conclusão

O desenvolvimento deste Totem de Autoatendimento Acessível representa uma evolução técnica significativa na criação de interfaces computacionais inclusivas e autônomas. A combinação de algoritmos de processamento de áudio em tempo real, mapeamento dinâmico em SVG embutido na conversa, controles flexíveis de privacidade (pausa) e interfaces adaptativas de alto contraste atende com primor às demandas técnicas e legais de acessibilidade. A estruturação inteligente de contexto baseada em histórico de turnos e catálogo de produtos superou a fragilidade comum dos chatbots tradicionais de autoatendimento, entregando conversações naturais, assertivas e de altíssima velocidade operacional. O projeto demonstra a viabilidade prática da Engenharia de Computação no desenvolvimento de soluções de impacto social e comercial direto.

---

## 7. Referências

1. **Associação Brasileira de Normas Técnicas (ABNT)**. *NBR 9050: Acessibilidade a edificações, mobiliário, espaços e equipamentos urbanos*. Rio de Janeiro, 2020.
2. **Brasil**. *Lei nº 13.146, de 6 de julho de 2015. Institui a Lei Brasileira de Inclusão da Pessoa com Deficiência (Estatuto da Pessoa com Deficiência)*. Diário Oficial da União, Brasília, 2015.
3. **FastAPI Framework**. *FastAPI Documentation: Concurrency and async / await*. Disponível em: <https://fastapi.tiangolo.com/>. Acesso em: 2026.
4. **Groq Technologies**. *LPU Inference Engine Performance and LLM Architectures*. Disponível em: <https://groq.com/>. Acesso em: 2026.
5. **Ultralytics**. *YOLOv8 Documentation: Real-time Object Detection and Intent Models*. Disponível em: <https://docs.ultralytics.com/>. Acesso em: 2026.
6. **W3C**. *Web Content Accessibility Guidelines (WCAG) 2.1*. Disponível em: <https://www.w3.org/TR/WCAG21/>. Acesso em: 2026.
