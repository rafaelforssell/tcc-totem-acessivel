# PRD — Totem de Autoatendimento Acessível
## Product Requirements Document · v3.0
**Projeto:** TCC — Engenharia da Computação · UNISANTA  
**Equipe:** Davi Xavier de Lima · Kauã Santos Silva · Rafael Luiz Forssell Ferrara Fomin  
**Orientador:** Sergio Schina de Andrade  
**Revisão:** Abril / 2026

---

## 1. Visão do Produto

O **Totem de Autoatendimento Acessível** é um sistema embarcado de consulta por voz e texto para lojas físicas de varejo, com foco principal em **acessibilidade para pessoas com deficiência visual**. O sistema permite que qualquer usuário — incluindo aqueles com mobilidade reduzida ou baixa literacia digital — encontre produtos, consulte preços, localizações e disponibilidade de estoque por meio de linguagem natural falada ou digitada.

> **Missão:** Tornar a experiência de compra em lojas físicas completamente autônoma e acessível para todos os perfis de usuário, eliminando a dependência de atendimento humano para consultas informacionais.

---

## 2. Problema

Lojas físicas de varejo enfrentam dois desafios simultâneos:

1. **Exclusão de pessoas com deficiência visual** — totens tradicionais dependem exclusivamente de interação visual (telas touch, teclados), tornando-se inacessíveis.
2. **Sobrecarga de atendentes** — perguntas repetitivas sobre localização de produtos, preços e estoque consomem tempo de profissionais que poderiam focar em vendas consultivas.

Não existe, no mercado nacional de médio porte, uma solução integrada e acessível que resolva ambos os problemas simultaneamente com baixo custo de implementação.

---

## 3. Usuários-Alvo

| Perfil | Características | Necessidade Principal |
|---|---|---|
| **Comprador com DV** | Deficiência visual parcial ou total | Consulta 100% por voz, feedback sonoro |
| **Comprador comum** | Sem deficiência, pressa ou timidez | Autoatendimento rápido sem fila |
| **Idoso / Baixa literacia** | Dificuldade com interfaces digitais | Linguagem natural simples |
| **Operador da loja** | Gerente ou atendente | Atualizar banco de produtos facilmente |

---

## 4. Objetivos e Métricas de Sucesso

### Objetivos Acadêmicos (TCC)
- Demonstrar viabilidade técnica de IA conversacional embarcada em hardware de custo acessível
- Implementar pipeline completo: entrada por voz → NLU → busca → síntese de voz
- Validar usabilidade com ao menos 5 usuários reais (incluindo PcD visual)

### Métricas de Sucesso do Sistema
| Métrica | Meta |
|---|---|
| Tempo médio de resposta (voz → áudio de volta) | ≤ 4 segundos |
| Taxa de reconhecimento correto de intenção | ≥ 85% |
| Taxa de acerto na busca de produto | ≥ 80% das consultas |
| Uptime do backend | ≥ 95% |
| Taxa de satisfação do usuário (escala Likert) | ≥ 4/5 |

---

## 5. Arquitetura Técnica Atual

### Stack Tecnológico

| Camada | Tecnologia | Função |
|---|---|---|
| **Frontend** | HTML5 + CSS3 + JS Vanilla | Interface web responsiva do totem |
| **Backend API** | Python 3 + FastAPI + Uvicorn | Servidor assíncrono REST |
| **STT** | Groq API (Whisper Large v3 Turbo) | Transcrição de áudio para texto |
| **NLU / Classificação** | Groq API (LLaMA 3.3 70B) | Classificação de intenção |
| **LLM Resposta** | Groq API (LLaMA 3.3 70B) | Geração de resposta contextualizada |
| **TTS** | Microsoft Edge TTS (pt-BR-FranciscaNeural) | Síntese de voz em português |
| **Banco de Dados** | SQLite3 | Catálogo de produtos com 16 SKUs |
| **Deploy** | Render (cloud free tier) | Hospedagem do backend |
| **Containerização** | Docker | Ambiente reproduzível |

### Módulos do Sistema

```
tcc-totem-acessivel/
├── frontend/
│   └── index.html              # UI completa (single-file app)
├── backend/
│   ├── main.py                 # FastAPI app + CORS + rotas legadas
│   ├── routes/
│   │   ├── query.py            # /query-text e /query-audio
│   │   └── produtos.py         # /produtos (listagem)
│   └── services/
│       ├── pipeline_service.py # Orquestrador principal (intenção → busca → resposta)
│       ├── llm_service.py      # Integração Groq (classificação + resposta LLM)
│       ├── stt_service.py      # Groq Whisper (áudio → texto)
│       ├── tts_service.py      # Edge TTS (texto → áudio MP3)
│       └── produtos_service.py # Acesso ao banco de dados
├── database/
│   ├── produtos.db             # SQLite com catálogo de 16 produtos
│   ├── init_db.py              # Script de seed do banco
│   └── create_db.py            # Script de criação do schema
└── Dockerfile                  # Containerização para deploy
```

---

## 6. Pipeline de Processamento (Fluxo Principal)

```
[Usuário fala]
      ↓
[Captura de áudio – MediaRecorder API]
      ↓
[Detecção de silêncio – Web Audio API]
      ↓
[POST /query-audio – envio do blob WebM]
      ↓
[STT – Groq Whisper → texto transcrito]
      ↓
[Classificação de intenção – LLaMA 3.3]
      │
      ├── NOVA_BUSCA → buscar_produtos_sql() → contexto DB
      ├── SOBRE_PRODUTO → usar memória de sessão
      └── OUTROS → resposta casual / despedida
      ↓
[perguntar_llm() – resposta contextualizada]
      ↓
[TTS – Edge TTS → MP3]
      ↓
[Retorno JSON: transcrição + resposta + produtos + URL do áudio]
      ↓
[Frontend reproduz áudio + exibe cards de produto]
```

---

## 7. Funcionalidades Implementadas (v1.0 – atual)

| ID | Funcionalidade | Status |
|---|---|---|
| F-01 | Captura de voz via microfone do navegador | ✅ Implementado |
| F-02 | Detecção automática de silêncio (1,5s) | ✅ Implementado |
| F-03 | Transcrição de áudio via Groq Whisper | ✅ Implementado |
| F-04 | Classificação de intenção (NOVA_BUSCA / SOBRE_PRODUTO / OUTROS) | ✅ Implementado |
| F-05 | Busca AND/OR com ranqueamento por relevância no SQLite | ✅ Implementado |
| F-06 | Memória de sessão (últimos 3 produtos) | ✅ Implementado |
| F-07 | Filtro inteligente de produtos citados na conversa | ✅ Implementado |
| F-08 | Geração de resposta LLM contextualizada (sem alucinação) | ✅ Implementado |
| F-09 | Síntese de voz em português (Edge TTS - Francisca Neural) | ✅ Implementado |
| F-10 | Interface de chat (bolhas de mensagem + cards de produto) | ✅ Implementado |
| F-11 | Encerramento automático de sessão por intenção | ✅ Implementado |
| F-12 | Entrada por texto alternativa ao microfone | ⚠️ UI parcial (ícone sem lógica) |
| F-13 | Deploy cloud (Render) | ✅ Implementado |
| F-14 | Containerização Docker | ✅ Implementado |

---

## 8. Funcionalidades Planejadas (v2.0 – próximas iterações)

| ID | Funcionalidade | Prioridade |
|---|---|---|
| F-15 | Entrada por texto totalmente funcional | ALTA |
| F-16 | Painel administrativo de produtos (CRUD) | ALTA |
| F-17 | Modo de alto contraste / acessibilidade visual | ALTA |
| F-18 | Histórico de conversa persistente por sessão | MÉDIA |
| F-19 | Multi-idioma (Libras / inglês) | BAIXA |
| F-20 | Mapa visual da loja com localização de produto | BAIXA |
| F-21 | Integração com sistema de estoque real (ERP) | BAIXA |
| F-22 | Autenticação e log de consultas | MÉDIA |
| F-23 | Testes automatizados (backend + pipeline) | ALTA |
| F-24 | Avaliação de usabilidade (SUS / escala Likert) | MÉDIA |

---

## 9. Requisitos Não-Funcionais

### Acessibilidade
- Todo feedback deve ter equivalente sonoro (TTS)
- Interface deve funcionar com leitor de tela (ARIA labels)
- Contraste mínimo WCAG AA em todos os elementos de texto
- Tamanho de fonte mínimo 16px para elementos interativos

### Performance
- Latência total STT → TTS ≤ 4 segundos em conexão 4G
- Backend deve suportar ao menos 5 requisições simultâneas

### Segurança
- Chaves de API armazenadas em variáveis de ambiente (.env)
- CORS configurado para origens controladas em produção
- Sem armazenamento de dados biométricos ou PII

### Manutenibilidade
- Código modularizado por responsabilidade (services, routes)
- Banco de dados populado via scripts versionados
- Deploy reproduzível via Docker

---

## 10. Restrições e Premissas

| Item | Detalhe |
|---|---|
| **Hardware** | Qualquer dispositivo com microfone e navegador moderno |
| **Conectividade** | Requer internet para chamadas às APIs (Groq, Edge TTS) |
| **Custo** | Groq API gratuita (tier free); Edge TTS gratuita |
| **Idioma** | Português brasileiro (pt-BR) como idioma primário |
| **Banco de dados** | SQLite para protótipo; migrável para PostgreSQL em produção |
| **Escopo** | Catálogo de roupas (Forssell Store) para fins de demonstração |

---

## 11. Riscos Identificados

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Groq API fica indisponível | Baixa | Alta | Fallback para OpenRouter / Ollama local |
| Limite de requisições Groq | Média | Alta | Cache de respostas frequentes |
| Edge TTS fora do ar | Baixa | Média | Fallback para gTTS ou pyttsx3 |
| Render cold start (boot lento) | Alta | Média | Keep-alive ping periódico |
| Ruído ambiente prejudica STT | Alta | Alta | Threshold de silêncio ajustável |
| Alucinação do LLM | Média | Alta | Prompt engineering + zero-temperature |

---

## 12. Roadmap

```
Fase 1 (Concluída): Protótipo Funcional
├── Pipeline de voz completo
├── Integração Groq (STT + LLM)
├── Banco SQLite com produtos
├── Interface de chat
└── Deploy no Render

Fase 2 (Em andamento): Consolidação e Qualidade
├── Entrada por texto funcional
├── Testes automatizados
├── Painel administrativo
├── Acessibilidade WCAG AA
└── Avaliação com usuários reais

Fase 3 (Planejada): Evolução e Entrega do TCC
├── Documentação acadêmica completa
├── Análise de resultados
├── Apresentação final
└── Possível hardware embarcado (Raspberry Pi)
```

---

*Documento vivo — atualizar conforme evolução do projeto.*  
*Versão anterior: PRD-2.0 | Próxima revisão planejada: Maio/2026*
