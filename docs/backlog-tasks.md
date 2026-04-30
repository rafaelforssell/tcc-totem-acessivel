# Backlog de Tasks — Totem Acessível
**Projeto:** TCC — Totem de Autoatendimento Acessível  
**Versão do Backlog:** 1.1 · Abril/2026  
**Referência:** PRD-3.0

---

> **Como usar este backlog:**
> - As tasks estão agrupadas por épico/tema
> - Cada task tem: ID, título, descrição técnica e lista de entregáveis
> - Prioridades: 🔴 Alta · 🟡 Média · 🟢 Baixa

---

## ÉPICO 1 — Interface e Experiência do Usuário

---

### TASK-01 · 🔴 Implementar entrada por texto funcional

**Problema:** O ícone de envio de texto existe na UI mas não possui lógica associada.

**O que fazer:**
- Conectar o campo `<input>` e o botão de envio ao endpoint `GET /query-text?q=`
- Exibir mensagem do usuário e resposta do totem no chat
- Não reproduzir áudio automaticamente na entrada por texto (opcional ao usuário)
- Permitir envio via tecla `Enter` além do clique no botão
- Usuário digita uma mensagem e tecla Enter ou clica no ícone → resposta aparece no chat
- Mensagem do usuário aparece na bolha direita, resposta do totem na bolha esquerda
- Sem erros no console

---

### TASK-02 · 🔴 Adicionar modo de alto contraste / acessibilidade visual

**Problema:** A interface atual tem boas cores para olhos saudáveis, mas não atende WCAG AA para DV parcial.

**O que fazer:**
- Criar botão de alternância de tema (normal ↔ alto contraste) no header
- No modo alto contraste: fundo preto, texto branco, bordas amarelas, sem gradientes
- Salvar preferência no `localStorage`
- Adicionar `aria-label` em todos os botões interativos
- Adicionar `role="log"` no container de chat para leitores de tela
- Contraste mínimo 4.5:1 em todos os textos (WCAG AA)
- Botão de alternância funciona e persiste ao recarregar
- Leitores de tela anunciam as novas mensagens do chat

---

### TASK-03 · 🟡 Adicionar indicador visual de nível de volume do microfone

**Problema:** Usuário não sabe se o microfone está captando a sua voz.

**O que fazer:**
- Usar o `AnalyserNode` já existente para mostrar barras de volume ao lado do botão de microfone
- Animação simples com 3-5 barras verticais que sobem/descem com o volume
- Barras animam em resposta ao volume capturado
- Barras param quando sessão é encerrada

---

### TASK-04 · 🟡 Melhorar cards de produto com mais informações

**Problema:** Cards atuais exibem apenas nome e preço, mas o banco tem setor, corredor e prateleira.

**O que fazer:**
- Adicionar ao card: setor + corredor + prateleira (localização na loja), tamanho, cor, estoque
- Adicionar ícone de localização antes dos dados de corredor/prateleira
- Estilo compacto (não aumentar muito o card)
- Card exibe: nome, preço, tamanho, cor, localização (setor/corredor/prateleira), estoque
- Layout não quebra em telas menores

---

### TASK-05 · 🟢 Adicionar tela de boas-vindas / splash screen

**Problema:** A interface abre direto no chat sem orientar o usuário sobre como usar o totem.

**O que fazer:**
- Criar uma tela inicial com instrução de uso ("Toque no microfone e faça sua pergunta")
- Ícones grandes e texto em fonte grande (≥ 20px) para acessibilidade
- Botão de iniciar que leva para o chat
- Totem fala a instrução automaticamente ao carregar (TTS local ou Edge TTS)
- Splash screen aparece ao abrir a página
- Botão "Iniciar" leva para o chat
- Mensagem de boas-vindas é lida em voz alta

---

## ÉPICO 2 — Backend e Pipeline de IA

---

### TASK-06 · 🔴 Implementar testes automatizados do pipeline

**Problema:** Não há nenhum teste automatizado no projeto, aumentando risco de regressões.

**O que fazer:**
- Criar arquivo `backend/tests/test_pipeline.py` com `pytest`
- Testes unitários para `buscar_produtos_sql()` com queries variadas
- Testes de integração para `pipeline_processar()` com mock da API Groq
- Teste de edge cases: query vazia, produto inexistente, intenção ambígua
- `pytest` roda sem erros com `python -m pytest backend/tests/`
- Cobertura mínima de 70% nas funções do `pipeline_service.py`

---

### TASK-07 · 🔴 Implementar cache de respostas frequentes

**Problema:** Perguntas idênticas fazem chamadas repetidas às APIs pagas da Groq, aumentando latência e consumindo cota.

**O que fazer:**
- Implementar cache em memória (dicionário Python) ou Redis para respostas do `perguntar_llm()`
- Chave de cache: hash(pergunta + hash(contexto))
- TTL de 10 minutos para invalidar respostas stale
- Log de hits/misses no console
- Pergunta repetida retorna em < 100ms (sem chamada à API)
- Cache invalida após TTL configurado
- Não quebra respostas diferentes para contextos diferentes

---

### TASK-08 · 🟡 Melhorar detecção de intenção com histórico de conversa

**Problema:** O classificador de intenção só vê a pergunta atual, sem contexto das mensagens anteriores.

**O que fazer:**
- Passar as últimas 2-3 mensagens do histórico para o prompt de `classificar_intencao()`
- Isso permite resolver referências como "e a vermelha?" após ter pesquisado uma camiseta
- Limitar histórico a N mensagens para não ultrapassar max_tokens
- "Ela tem em vermelho?" após busca de camiseta é classificado como SOBRE_PRODUTO
- Histórico não ultrapassa 3 mensagens anteriores no prompt

---

### TASK-09 · 🟡 Implementar fallback para quando Groq API está indisponível

**Problema:** Se a Groq API retornar erro, o usuário recebe uma mensagem de erro genérica sem alternativa.

**O que fazer:**
- Implementar retry com exponential backoff (3 tentativas)
- Se todas as tentativas falharem, tentar OpenRouter como fallback
- Resposta de fallback amigável se tudo falhar: "Estou com dificuldades técnicas. Tente novamente em instantes."
- Sistema faz até 3 retentativas com backoff em caso de erro HTTP 5xx
- OpenRouter é chamado se Groq falhar definitivamente
- Mensagem amigável em caso de falha total

---

### TASK-10 · 🟢 Adicionar logging estruturado no backend

**Problema:** Os logs atuais usam `print()`, dificultando análise em produção.

**O que fazer:**
- Substituir todos os `print()` por `logging` do Python
- Formato: timestamp + nível + módulo + mensagem
- Salvar logs em arquivo rotativo `backend/logs/app.log`
- Logar: tempo de cada etapa (STT, NLU, LLM, TTS), intenção classificada, número de resultados
- Zero `print()` nos arquivos de serviço
- Arquivo de log criado automaticamente
- Log inclui tempo de cada etapa do pipeline

---

## ÉPICO 3 — Banco de Dados e Dados

---

### TASK-11 · 🔴 Criar painel administrativo de produtos (CRUD)

**Problema:** Para adicionar, editar ou remover produtos, é necessário alterar manualmente o `init_db.py` e recriar o banco.

**O que fazer:**
- Criar rota `GET /admin/produtos` — lista todos os produtos
- Criar rota `POST /admin/produtos` — adiciona produto
- Criar rota `PUT /admin/produtos/{id}` — edita produto
- Criar rota `DELETE /admin/produtos/{id}` — remove produto
- Criar página HTML simples `frontend/admin.html` com formulário de CRUD
- Proteger com token estático (variável de ambiente `ADMIN_TOKEN`)
- CRUD funcional via interface web
- Sem autenticação → retorna 401
- Alterações persistem no banco SQLite

---

### TASK-12 · 🟡 Adicionar busca por similaridade fonética

**Problema:** Erros de pronúncia ou transcrição ("calça" → "calsa") fazem a busca falhar.

**O que fazer:**
- Implementar normalização de texto (remover acentos, lowercase, plural → singular básico)
- Considerar biblioteca `fuzzywuzzy` ou `rapidfuzz` para distância de edição
- Aplicar na função `buscar_produtos_sql()` como pré-processamento das palavras-chave
- "calsa" encontra "Calça Jeans Slim"
- "camiza" encontra "Camiseta Básica"
- Performance não degrada mais de 200ms

---

### TASK-13 · 🟡 Expandir catálogo de produtos (50+ SKUs)

**Problema:** O banco atual tem apenas 16 produtos, insuficiente para testes realistas de busca e relevância.

**O que fazer:**
- Expandir para ao menos 50 produtos diversificados (mais categorias, marcas, cores, tamanhos)
- Incluir categorias: Calçados, Acessórios, Agasalhos
- Manter script `init_db.py` como fonte da verdade
- Documentar estrutura de dados no README da pasta `/database`
- Banco com ≥ 50 produtos após rodar `init_db.py`
- Ao menos 5 categorias distintas
- Nenhum produto duplicado

---

### TASK-14 · 🟢 Criar endpoint de saúde do sistema (health check)

**Problema:** Não há como monitorar se o backend está funcionando sem fazer uma query de verdade.

**O que fazer:**
- Criar `GET /health` que retorna: status do servidor, status da conexão com BD, timestamp
- Retornar HTTP 200 se tudo OK, HTTP 503 se BD inacessível
- `GET /health` retorna `{ "status": "ok", "db": "ok", "timestamp": "..." }`
- Retorna 503 se BD estiver corrompido ou inacessível

---

## ÉPICO 4 — DevOps e Qualidade

---

### TASK-15 · 🔴 Configurar CI/CD com GitHub Actions

**Problema:** Deploy no Render é manual; não há verificação automática de qualidade de código.

**O que fazer:**
- Criar `.github/workflows/ci.yml`
- Pipeline: lint com `flake8` → testes com `pytest` → build Docker
- Gatilho: push em qualquer branch + PR para `main`
- Badge de status no README
- GitHub Actions executa em todo push
- PR bloqueado se testes ou lint falharem
- Badge verde no README quando tudo passa

---

### TASK-16 · 🟡 Otimizar Dockerfile para reduzir tamanho da imagem

**Problema:** Imagem Docker atual pode ser grande por incluir dependências de build desnecessárias.

**O que fazer:**
- Usar multi-stage build (build stage + runtime stage)
- Usar `python:3.11-slim` como base
- Remover arquivos temporários e caches no Dockerfile
- Adicionar `.dockerignore` adequado
- Imagem final < 500MB
- Container inicia em < 10 segundos
- Funcionalidade 100% preservada

---

### TASK-17 · 🟡 Implementar keep-alive para evitar cold start no Render

**Problema:** O Render free tier hiberna a aplicação após 15 minutos de inatividade, causando latência de 30-60 segundos no primeiro acesso.

**O que fazer:**
- Adicionar script de ping periódico (a cada 14 minutos) via serviço externo (UptimeRobot) ou cron job
- Ou implementar no próprio frontend um ping silencioso `GET /health` periódico
- Aplicação responde em < 2 segundos a qualquer hora do dia
- Ping não gera logs desnecessários

---

### TASK-18 · 🟢 Criar documentação da API (OpenAPI / Swagger)

**Problema:** Não há documentação formal dos endpoints disponíveis.

**O que fazer:**
- FastAPI já gera `/docs` (Swagger UI) e `/redoc` automaticamente
- Adicionar docstrings em português em cada rota e parâmetro
- Adicionar exemplos de request/response nas rotas principais
- `GET /docs` abre interface Swagger funcional
- Todas as rotas têm descrição e exemplo de uso

---

## ÉPICO 5 — Pesquisa e Validação Acadêmica

---

### TASK-19 · 🔴 Conduzir avaliação de usabilidade com usuários reais

**Problema:** Sem dados empíricos, a afirmação de "acessibilidade" é apenas teórica.

**O que fazer:**
- Preparar roteiro de teste com 5 cenários de uso (busca simples, busca por localização, pergunta de seguimento, despedida, produto inexistente)
- Aplicar com ao menos 5 participantes (incluir ao menos 1 pessoa com DV)
- Usar escala SUS (System Usability Scale) + escala Likert personalizada
- Registrar: tempo de tarefa, erros, satisfação, comentários qualitativos
- Relatório de usabilidade com resultados quantitativos e qualitativos
- SUS Score calculado e interpretado
- Incorporado ao documento do TCC

---

### TASK-20 · 🟡 Documentar resultados de performance do pipeline

**Problema:** Não há métricas registradas sobre o tempo real de cada etapa do pipeline.

**O que fazer:**
- Executar 50 consultas de teste e registrar o tempo de: STT, NLU, LLM, TTS, total
- Calcular média, mediana, percentil 95
- Gerar gráfico comparativo por etapa
- Documentar no TCC como "Análise de Performance"
- Dataset de 50 consultas com tempos registrados
- Tabela de métricas estatísticas
- Gráfico de barras por etapa

---

### TASK-21 · 🟢 Pesquisar e comparar alternativas de STT e TTS

**Problema:** A escolha de Groq Whisper e Edge TTS foi pragmática; não há comparação formal com alternativas.

**O que fazer:**
- Comparar STT: Groq Whisper vs OpenAI Whisper vs AssemblyAI vs Deepgram (custo, latência, acurácia em pt-BR)
- Comparar TTS: Edge TTS vs Google TTS vs ElevenLabs (naturalidade, latência, custo)
- Justificar escolha atual com dados
- Incorporar como seção de fundamentação técnica no TCC
- Tabela comparativa de STT e TTS publicada no documento do TCC
- Justificativa técnica e econômica da escolha atual

---

## Resumo do Backlog

| Épico | Tarefas | 🔴 Alta | 🟡 Média | 🟢 Baixa |
|---|---|---|---|---|
| 1 — Interface e UX | 5 | 2 | 2 | 1 |
| 2 — Backend e IA | 5 | 2 | 2 | 1 |
| 3 — Banco de Dados | 4 | 1 | 2 | 1 |
| 4 — DevOps | 4 | 1 | 2 | 1 |
| 5 — Pesquisa Acadêmica | 3 | 1 | 1 | 1 |
| **Total** | **21** | **7** | **9** | **5** |

---

*Backlog vivo — revisar e priorizar semanalmente conforme evolução do TCC.*
