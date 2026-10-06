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
   4.3.4 Configuração dos Modelos de IA e Mecanismos de Fallback  
   4.4 Lógica de Interface e Interação no Front-end  
   4.4.1 Fluxo de Captura de Áudio, Detecção de Silêncio e MediaRecorder  
   4.4.2 Lógica de Pausa Ativa de Sessão e Privacidade  
   4.4.3 Renderização Dinâmica de Rota Indoor sobre SVG no Chat  
   4.4.4 Modal Lightbox para Ampliação e Carrossel de Imagens  
   4.4.5 Suporte a Alto Contraste e Acessibilidade Visual  
   4.5 Segurança e Privacidade  
5. **Resultados e Testes**  
   5.1 Ambiente de Validação  
   5.2 Testes Funcionais  
   5.3 Bateria de Testes Conversacionais  
   5.4 Métricas Quantitativas  
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
│   ├── audios/                 # Áudios temporários (apagados automaticamente)
│   ├── avaliacao/              # Scripts e frases da bateria de testes e métricas
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
3. **TTS (Síntese)**: A resposta textual gerada pela IA é enviada para o serviço de áudio Edge-TTS, que gera um arquivo MP3 sob demanda, tocado imediatamente no front-end e removido do servidor após o período de retenção (seção 4.5).

Cada etapa tem seu tempo medido individualmente, e a rota devolve esses valores (`tempos`: STT, IA, TTS e total), permitindo o cálculo das métricas de latência apresentadas na seção 5.4.

#### 4.3.2 Lógica de Memória Conversacional e Persistência de Turnos
O maior diferencial de inteligência e acessibilidade do Totem é o objeto `memoria` controlado no `pipeline_service.py`. Cada sessão de atendimento possui sua própria memória, com a seguinte estrutura:

```python
{
    "ultimos_produtos": [],                # produtos da última resposta
    "assunto_ativo": None,                 # assunto corrente da conversa
    "historico_conversas": [],             # turnos usuário/assistente
    "produtos_mencionados": {},            # todos os produtos citados, por ID
    "produtos_escolhidos": [],             # produtos que o cliente confirmou querer
    "produtos_pendentes_confirmacao": [],  # opções aguardando "gostei"/"sim"
    "tentativas_silencio": 0,              # silêncios seguidos (encerra no 2º)
    "genero": None,                        # público (masculino/feminino) inferido
    "tipo_ativo": None,                    # tipo de peça herdado entre turnos
}
```

A memória é isolada por sessão: o front-end gera um identificador aleatório por aba do navegador (`X-Session-Id`) e o envia em cada requisição, de modo que dois totens ligados ao mesmo servidor não compartilham conversas. As sessões ficam em memória RAM, expiram após 30 minutos de inatividade e são limitadas a 200 simultâneas; o comando de reinício (`/reset`) limpa apenas a sessão de quem o chamou.

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

#### 4.3.4 Configuração dos Modelos de IA e Mecanismos de Fallback
A Tabela 1 resume a configuração final dos modelos utilizados no projeto.

**Tabela 1 – Configuração dos modelos de IA**

| Etapa | Modelo / serviço | Parâmetros |
|---|---|---|
| STT (transcrição) | `whisper-large-v3-turbo` via API Groq | idioma `pt`, timeout de 30 s |
| Classificação de intenção | `llama-3.3-70b-versatile` via API Groq | temperatura 0,0; `max_tokens` 512; saída em JSON (`response_format: json_object`); timeout de 20 s |
| Geração da resposta | `llama-3.3-70b-versatile` via API Groq | temperatura 0,0; `max_tokens` 1000; últimas 10 mensagens do histórico; timeout de 20 s |
| TTS (síntese de voz) | Edge-TTS, voz `pt-BR-FranciscaNeural` | saída em MP3 |

A temperatura 0,0 foi adotada nas duas chamadas ao LLM para tornar as respostas determinísticas e reduzir a chance de o modelo inventar informações que não estejam no banco de dados.

Para manter o totem operante quando a API não responde (falha de rede, indisponibilidade ou limite de requisições, HTTP 429), foram implementados os seguintes mecanismos de contingência:
- **LLM**: a classificação de intenção passa a ser feita por regras locais de palavras-chave (despedidas, pedidos de mapa e extração de termos de busca), e a resposta é montada a partir de modelos de frase com os dados do produto. Não há um segundo modelo de linguagem.
- **STT**: há suporte opcional a transcrição local com o modelo Whisper `tiny` (pacote `openai-whisper`). Como esse pacote não faz parte das dependências de implantação, o fallback de transcrição está disponível apenas no ambiente de desenvolvimento em que ele tiver sido instalado; no servidor em nuvem, uma falha da API resulta em transcrição vazia, e o totem pede que o usuário repita.

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

### 4.5 Segurança e Privacidade

Por lidar com a voz de clientes e com um painel de gestão de estoque, o back-end adota as seguintes medidas:

- **Chaves e segredos**: nenhuma chave fica no código-fonte. As credenciais (Groq, Telegram, banco de dados e painel administrativo) são lidas de variáveis de ambiente, e o arquivo `.env` não é versionado.
- **Painel administrativo**: as rotas de gestão exigem o cabeçalho `X-Admin-Key`. Não existe chave padrão: sem a variável `ADMIN_KEY`, o painel permanece desativado (HTTP 503). A comparação da chave é feita em tempo constante (`hmac.compare_digest`), evitando ataques de temporização.
- **CORS**: a API só aceita chamadas do front-end publicado (`https://totem-acessiveltcc.netlify.app`) e, para desenvolvimento, do `localhost`; outros domínios podem ser definidos pela variável `CORS_ORIGINS`. A API não usa cookies, portanto as requisições entre origens são aceitas sem credenciais, e apenas os métodos e cabeçalhos usados pelo front-end são liberados.
- **Rota de saúde (`/health`)**: informa apenas o estado do serviço, do banco e a quantidade de produtos. Não revela quais integrações estão configuradas, e detalhes de erros do banco ficam somente no log do servidor.
- **Retenção de áudio**: o áudio gravado do cliente é apagado logo após o processamento, inclusive quando alguma etapa falha. Os áudios de resposta gerados pelo TTS são removidos automaticamente após 10 minutos (configurável por `AUDIO_RETENCAO_SEGUNDOS`), e nenhum áudio é versionado no repositório.
- **Memória conversacional**: mantida apenas em RAM, isolada por sessão e descartada após 30 minutos de inatividade, ao encerrar o atendimento ou ao reiniciar o servidor. Nenhuma conversa é gravada em disco.

**Limitações conhecidas**: a chave do painel administrativo é guardada no `localStorage` do navegador do operador; as sessões em RAM não são compartilhadas entre múltiplas instâncias do servidor; e o identificador de sessão não é autenticado, sendo adequado a um totem em ambiente controlado, mas não a um serviço público aberto.

---

## 5. Resultados e Testes

### 5.1 Ambiente de Validação

**Tabela 2 – Ambiente utilizado nos testes**

| Item | Configuração |
|---|---|
| Front-end | Hospedado no Netlify (https://totem-acessiveltcc.netlify.app) |
| Back-end | Python 3.10, FastAPI 0.136.1, hospedado no Render (nuvem) |
| Banco de dados | **[PREENCHER: SQLite local ou PostgreSQL no Render]** |
| Navegador | Google Chrome 154.0.8037.98 |
| Sistema operacional | Windows 11 Home Single Language, 64 bits |
| Hardware | Processador AMD Ryzen 5 5600, 16 GB de RAM |
| Microfone | Kaidi KMF4-C |
| Conexão | Wi-Fi |

Por gravar o áudio no formato WebM por meio da API `MediaRecorder`, o front-end é compatível com navegadores baseados em Chromium (Chrome e Edge) e com o Firefox; o Safari não grava nesse formato.

### 5.2 Testes Funcionais

Os testes sistemáticos de integração do Totem Acessível comprovaram a robustez das soluções implementadas:
1. **Teste de Normalização**: A frase em áudio *"Quero duas camisetas de treino"* foi transcrevida com sucesso. O LLM extraiu apenas `["camisa", "treino"]` como palavras-chave, localizando perfeitamente as opções de **Camisa Dry Fit** no SQLite.
2. **Teste de Conversação e Detalhes**: Em conformidade com o novo fluxo de detalhes, ao buscar a camisa de treino, a IA apresentou primeiro todos os detalhes (tecido dry fit respirável da Nike, cor preta, tamanho GG e valor de R$ 79,90) e finalizou perguntando se o usuário gostou da opção. Ao responder *"sim"*, o mapa com a rota destacando o **Corredor 2** foi renderizado perfeitamente no fluxo da conversa.
3. **Teste de Memória Conversacional**: Buscamos consecutivamente 5 produtos diferentes na mesma sessão. No final, ao perguntarmos *"Quais foram os produtos que conversamos hoje?"*, a IA respondeu com sucesso gerando a listagem ordenada de todos os 5 produtos apresentados anteriormente.
4. **Teste de Terminação e Cancelamento**: Clicar em "Encerrar" no meio do processamento da IA cancelou a reprodução de áudio em tempo de execução, garantindo que o sistema ficasse mudo imediatamente ao retornar à tela inicial.

Além dos testes manuais, o back-end conta com uma suíte automatizada (`pytest`) que cobre o pipeline conversacional, a busca de produtos, o painel administrativo e as medidas de segurança da seção 4.5 (isolamento de sessões, remoção de áudios e conteúdo da rota `/health`).

### 5.3 Bateria de Testes Conversacionais

Para avaliar o classificador de intenções além de exemplos isolados, foi montado um conjunto de 75 frases em português (arquivo `backend/avaliacao/frases_intencoes.csv`), 15 por intenção, incluindo linguagem coloquial, gírias e frases incompletas:

**Tabela 3 – Exemplos da bateria de testes**

| Intenção | Exemplos |
|---|---|
| Nova busca (`NOVA_BUSCA`) | "tem calça jeans feminina?", "queria um short pra academia", "gostei do vestido. você tem cinto?" |
| Pergunta sobre produto (`SOBRE_PRODUTO`) | "quanto custa essa camisa?", "tem essa em tamanho M?", "ela é de algodão?" |
| Solicitação de mapa (`IR_PARA_MAPA`) | "onde fica?", "como eu chego lá?", "mostra todos no mapa" |
| Encerramento (`ENCERRAR`) | "valeu tchau", "não preciso de mais nada", "só isso mesmo valeu" |
| Fora do escopo (`OUTROS`) | "posso pagar no pix?", "vai chover hoje?", "qual a senha do wifi?" |

O script `avaliar_intencoes.py` envia cada frase ao classificador, compara a intenção obtida com a esperada e registra se a resposta veio do modelo de linguagem ou do fallback por regras, de forma que falhas da API não sejam contabilizadas como acertos ou erros do modelo.

Para a avaliação por voz, 30 dessas frases (6 por intenção, listadas em `backend/avaliacao/audios/referencias.csv`) foram gravadas **[PREENCHER: por quantas pessoas e em que ambiente]** e enviadas ao totem pelo script `avaliar_voz.py`, que utiliza a mesma rota `/query-audio` do front-end.

### 5.4 Métricas Quantitativas

- **Acurácia por intenção**: proporção de frases de cada intenção classificadas corretamente.
- **Latência p50 e p95**: mediana e percentil 95 do tempo de resposta, medidos no cliente (ponta a ponta) e por etapa no servidor.
- **WER (Word Error Rate)**: (substituições + deleções + inserções) ÷ número de palavras da referência, calculado após converter o texto para minúsculas e remover acentos e pontuação.

**Tabela 4 – Acurácia do classificador de intenções (n = 75)**

| Intenção | Acertos | Acurácia |
|---|---|---|
| Nova busca | **[PREENCHER]**/15 | **[PREENCHER]** % |
| Pergunta sobre produto | **[PREENCHER]**/15 | **[PREENCHER]** % |
| Solicitação de mapa | **[PREENCHER]**/15 | **[PREENCHER]** % |
| Encerramento | **[PREENCHER]**/15 | **[PREENCHER]** % |
| Fora do escopo | **[PREENCHER]**/15 | **[PREENCHER]** % |
| **Geral** | **[PREENCHER]**/75 | **[PREENCHER]** % |

**Tabela 5 – Latência e WER da interação por voz (n = [PREENCHER] áudios)**

| Métrica | p50 | p95 |
|---|---|---|
| Ponta a ponta (cliente) | **[PREENCHER]** s | **[PREENCHER]** s |
| STT | **[PREENCHER]** s | **[PREENCHER]** s |
| IA (pipeline + LLM) | **[PREENCHER]** s | **[PREENCHER]** s |
| TTS | **[PREENCHER]** s | **[PREENCHER]** s |
| **WER geral** | **[PREENCHER]** % | |

**[PREENCHER: análise dos resultados — intenções com mais erros, principais confusões da matriz, etapa mais lenta e exemplos de erros de transcrição.]**

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
