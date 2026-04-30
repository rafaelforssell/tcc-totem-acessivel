# Diagrama de Operação — Totem de Autoatendimento Acessível
**Formato:** Swimlane Horizontal · v1.0 · Abril/2026

---

## Fluxo Completo de uma Interação por Voz

```mermaid
sequenceDiagram
    autonumber

    actor U as 👤 Usuário
    participant FE as 🖥️ Frontend<br/>(Browser / HTML)
    participant BE as ⚙️ Backend<br/>(FastAPI)
    participant STT as 🎤 STT Service<br/>(Groq Whisper)
    participant NLU as 🧠 NLU Service<br/>(LLaMA 3.3)
    participant DB as 🗄️ Banco de Dados<br/>(SQLite)
    participant LLM as 💬 LLM Response<br/>(LLaMA 3.3)
    participant TTS as 🔊 TTS Service<br/>(Edge TTS)

    U->>FE: Toca no botão de microfone
    FE->>FE: Solicita permissão de microfone (getUserMedia)
    FE->>FE: Inicia gravação (MediaRecorder)
    FE->>FE: Monitora silêncio via Web Audio API
    Note over FE: Após 1,5s de silêncio → para gravação

    FE->>BE: POST /query-audio (blob WebM)
    
    BE->>STT: Envia arquivo de áudio
    STT-->>BE: Retorna texto transcrito (pt-BR)

    BE->>NLU: Envia texto → classificar_intencao()
    NLU-->>BE: JSON { intencao, palavras_chave }

    alt NOVA_BUSCA
        BE->>DB: buscar_produtos_sql(palavras_chave)
        DB-->>BE: Lista de produtos (AND → OR fallback)
        BE->>BE: Armazena top 3 na memória de sessão
    else SOBRE_PRODUTO
        BE->>BE: Recupera produtos da memória de sessão
        BE->>BE: Filtra produtos citados na pergunta
    else OUTROS (despedida)
        BE->>BE: Retorna resposta fixa de despedida
    end

    BE->>LLM: perguntar_llm(pergunta, contexto_produtos)
    LLM-->>BE: Resposta em texto (≤ 3 frases, sem markdown)

    BE->>TTS: falar(resposta_texto)
    TTS-->>BE: Arquivo MP3 gerado (UUID.mp3)

    BE-->>FE: JSON { transcricao, resposta, resultados[], audio_url }

    FE->>FE: Exibe bolha do usuário (transcrição)
    FE->>FE: Exibe bolha do totem (resposta)
    FE->>FE: Renderiza cards de produto (se houver)
    FE->>U: Reproduz áudio de resposta (TTS)

    alt Sessão continua
        FE->>FE: Volta a ouvir (conversar())
    else Despedida detectada
        FE->>FE: encerrarSessao()
    end
```

---

## Diagrama Swimlane Horizontal (Estilo Processo)

```mermaid
flowchart LR
    subgraph USER["👤 USUÁRIO"]
        U1([Fala / Digita]) --> U2([Ouve resposta])
    end

    subgraph FRONTEND["🖥️ FRONTEND — Browser"]
        F1[Captura áudio<br/>MediaRecorder] --> F2[Detecta silêncio<br/>Web Audio API]
        F2 --> F3[Envia blob WebM<br/>POST /query-audio]
        F7[Recebe JSON] --> F8[Exibe chat +<br/>cards de produto]
        F8 --> F9[Reproduz<br/>áudio TTS]
    end

    subgraph BACKEND["⚙️ BACKEND — FastAPI"]
        B1[Recebe áudio] --> B2[Chama STT]
        B2 --> B3[Texto transcrito]
        B3 --> B4[Chama NLU<br/>classificar_intencao]
        B4 --> B5{Intenção?}
        B5 --> B6[Chama LLM<br/>perguntar_llm]
        B6 --> B7[Chama TTS<br/>falar]
        B7 --> B8[Monta JSON<br/>de resposta]
    end

    subgraph SERVICES["🔌 SERVIÇOS EXTERNOS"]
        S1["🎤 Groq Whisper<br/>STT"]
        S2["🧠 LLaMA 3.3<br/>NLU + LLM"]
        S3["🔊 Edge TTS<br/>Francisca Neural"]
    end

    subgraph DATABASE["🗄️ BANCO DE DADOS"]
        D1[(SQLite<br/>produtos.db)]
        D2[Busca AND/OR<br/>com ranking]
        D3[Memória<br/>de Sessão]
    end

    U1 --> F1
    F3 --> B1
    B2 <--> S1
    B4 <--> S2
    B5 -- NOVA_BUSCA --> D1
    D1 --> D2 --> D3
    D3 --> B6
    B5 -- SOBRE_PRODUTO --> D3
    B6 <--> S2
    B7 <--> S3
    B8 --> F7
    F9 --> U2
```

---

## Fluxo de Classificação de Intenção (Detalhe)

```mermaid
flowchart TD
    A([Texto do usuário]) --> B[LLaMA 3.3<br/>classificar_intencao]
    B --> C{Intenção}

    C -->|NOVA_BUSCA| D[Extrair palavras-chave<br/>do produto]
    D --> E[buscar_produtos_sql<br/>cláusula AND]
    E --> F{Encontrou?}
    F -->|Sim| G[Salva top 3<br/>na memória]
    F -->|Não| H[Fallback OR<br/>com ranking]
    H --> G
    G --> I[Gera resposta<br/>com contexto]

    C -->|SOBRE_PRODUTO| J{Há memória?}
    J -->|Sim| K[Recupera últimos<br/>produtos]
    K --> L[Filtra por nome<br/>citado na pergunta]
    L --> I
    J -->|Não| M[Força NOVA_BUSCA]
    M --> D

    C -->|OUTROS| N{É despedida?}
    N -->|Sim| O[Resposta fixa<br/>Muito obrigado!]
    N -->|Não| P[Resposta casual<br/>via LLM]

    I --> Q([Resposta final])
    O --> Q
    P --> Q
```

---

## Diagrama de Componentes e Dependências

```mermaid
graph TB
    subgraph INFRA["☁️ Infraestrutura"]
        RENDER[Render.com<br/>Cloud Deploy]
        DOCKER[Docker Container]
    end

    subgraph APP["Aplicação"]
        MAIN[main.py<br/>FastAPI App]
        QROUTE[routes/query.py<br/>Endpoints]
        PROUTE[routes/produtos.py<br/>Endpoints]
        PIPELINE[services/pipeline_service.py<br/>Orquestrador]
        LLM[services/llm_service.py<br/>Groq Integration]
        STT[services/stt_service.py<br/>Whisper]
        TTS[services/tts_service.py<br/>Edge TTS]
        PRODUTOS[services/produtos_service.py<br/>DB Access]
    end

    subgraph DATA["Dados"]
        SQLITE[(database/produtos.db)]
        AUDIOS[/audios/*.mp3/]
        ENV[.env<br/>API Keys]
    end

    subgraph EXTERNAL["APIs Externas"]
        GROQ[Groq API<br/>api.groq.com]
        EDGETTS[Edge TTS<br/>Microsoft]
    end

    RENDER --> DOCKER --> MAIN
    MAIN --> QROUTE
    MAIN --> PROUTE
    QROUTE --> PIPELINE
    QROUTE --> STT
    QROUTE --> TTS
    PIPELINE --> LLM
    PIPELINE --> SQLITE
    PIPELINE --> PRODUTOS
    LLM --> GROQ
    STT --> GROQ
    TTS --> EDGETTS
    TTS --> AUDIOS
    LLM --> ENV
    STT --> ENV
```

---

*Diagramas gerados com Mermaid.js — renderizáveis no GitHub, Notion e VS Code (extensão Mermaid Preview)*
