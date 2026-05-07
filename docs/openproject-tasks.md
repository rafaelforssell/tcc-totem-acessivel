# Reconstrução de Rastreabilidade — Tarefas OpenProject

Este documento apresenta uma organização lógica retroativa do desenvolvimento do projeto **Totem de Autoatendimento Acessível**. Seu objetivo é servir como base para importação e cadastro na plataforma de gestão OpenProject, refletindo o caminho percorrido desde a concepção até o estado atual do repositório (ref. PRD 3.1).

---

### 1. Estruturação inicial do projeto
- **Épico:** Arquitetura Base
- **Task:** Configuração da estrutura de monorepo
- **Descrição:** Criar árvore de diretórios raiz (`frontend`, `backend`, `database`, `docs`, `assets`, `audios`), inicializar repositório Git e definir o `README.md` principal do projeto.
- **Critério de aceite:** Diretórios estabelecidos, README documentado e commit inicial gerado no GitHub.
- **Dependências:** Nenhuma.
- **Status sugerido:** Concluída

### 2. Configuração do backend FastAPI
- **Épico:** Arquitetura Base
- **Task:** Setup do servidor FastAPI e roteamento básico
- **Descrição:** Instanciar o servidor via FastAPI e Uvicorn, configurar middleware CORS para desenvolvimento local e definir a base dos roteadores (`main.py` e `routes/`).
- **Critério de aceite:** Servidor rodando localmente (porta 8000) e respondendo `200 OK` em rotas de teste.
- **Dependências:** 1
- **Status sugerido:** Concluída

### 3. Configuração do frontend
- **Épico:** Arquitetura Base
- **Task:** Scaffold do Single Page Application (SPA)
- **Descrição:** Criar o arquivo `index.html` com suporte ao framework Tailwind CSS (via CDN) e configuração inicial de fontes e cores do projeto.
- **Critério de aceite:** Renderização visual básica com aplicação do tema customizado (Kiosk) sem erros no console do navegador.
- **Dependências:** 1
- **Status sugerido:** Concluída

### 4. Integração com banco SQLite
- **Épico:** Backend e Dados
- **Task:** Instanciação do banco relacional local
- **Descrição:** Desenvolver o script de schema (`create_db.py`) e conexão base (`sqlite3`) para suportar a arquitetura sem dependência de banco em nuvem nesta fase.
- **Critério de aceite:** Criação bem-sucedida do arquivo físico `produtos.db` e scripts capazes de interagir com o DB sem locks.
- **Dependências:** 2
- **Status sugerido:** Concluída

### 5. Implementação da base de produtos
- **Épico:** Backend e Dados
- **Task:** Seed e preenchimento de catálogo de dados
- **Descrição:** Desenvolver script de população inicial (`init_db.py`) com um catálogo MVP de ~16 produtos cobrindo roupas e alimentos.
- **Critério de aceite:** Tabela `produtos` possuir colunas de localização (setor, corredor, prateleira), estoque e descrições populadas e reais.
- **Dependências:** 4
- **Status sugerido:** Concluída

### 6. Implementação do fluxo de busca de produtos
- **Épico:** Backend e Dados
- **Task:** Sistema de busca AND/OR com relevância
- **Descrição:** Criar o módulo capaz de buscar múltiplas palavras-chaves. Se o operador `AND` for restritivo demais e falhar, usar fallback em `OR` ranqueando pelos IDs com mais acertos.
- **Critério de aceite:** A função deve retornar resultados precisos para frases complexas e conseguir tratar erros gramaticais com o fallback OR.
- **Dependências:** 5
- **Status sugerido:** Concluída

### 7. Implementação do pipeline STT -> NLU/LLM -> Busca SQL -> Resposta LLM -> TTS
- **Épico:** Integração e IA
- **Task:** Orquestração linear do pipeline de inteligência
- **Descrição:** Construir o serviço principal (`pipeline_service.py`) que recebe o blob de áudio, aciona transcrição Whisper, extrai intenção com LLM (LLaMA 3.3), pesquisa no SQLite, gera nova resposta conversacional via LLM e devolve um áudio TTS.
- **Critério de aceite:** Processamento de ponta-a-ponta funcionando de forma fluida com tempos logados no terminal e arquivos `.mp3` e texto gerados como retorno.
- **Dependências:** 2, 6
- **Status sugerido:** Concluída

### 8. Implementação da gravação por voz
- **Épico:** Frontend e UX
- **Task:** Captura de microfone nativa
- **Descrição:** Integrar a `MediaRecorder API` ao botão de iniciar gravação no front-end para capturar fluxos em formato `audio/webm`.
- **Critério de aceite:** Navegador pede permissão de microfone e exporta BLOB binário validamente enviado via POST para a API do backend.
- **Dependências:** 3
- **Status sugerido:** Concluída

### 9. Implementação da detecção automática de silêncio
- **Épico:** Acessibilidade e Usabilidade
- **Task:** Gatilho sonoro contínuo com interrupção inteligente
- **Descrição:** Utilizar a `Web Audio API` para ler a amplitude de onda e, após detectar 1,5 segundos de inatividade (ruído nulo), interromper a gravação automaticamente (sem clique em tela).
- **Critério de aceite:** Usuário fala a frase, para de falar, e o sistema processa automaticamente a requisição após 1.5s.
- **Dependências:** 8
- **Status sugerido:** Concluída

### 10. Implementação da tela de chat
- **Épico:** Frontend e UX
- **Task:** Componente SPA de conversação (ChatUI)
- **Descrição:** Criar a seção (`<section id="screen2">`) que abriga as bolhas de mensagens e injeção do componente de "cards" compactos para devolução visual de listas de itens resultantes de uma consulta.
- **Critério de aceite:** As mensagens flutuam entre o robô e o usuário de acordo com o retorno da API. Renderização automática dos resultados em formato card.
- **Dependências:** 3, 7
- **Status sugerido:** Concluída

### 11. Implementação da tela de produto
- **Épico:** Frontend e UX
- **Task:** Componente SPA de Detalhes
- **Descrição:** Construir tela (`<section id="screen3">`) focada em apresentar a foto de um produto, valor, descrição formatada, marca, estoque, e um botão de chamado para exibição do mapa da loja.
- **Critério de aceite:** Ao tocar em "Ver Produto" ou via integração de voz, o usuário navega na SPA para uma visão ampla focada no item.
- **Dependências:** 3
- **Status sugerido:** Concluída

### 12. Implementação do mapa visual/interativo
- **Épico:** Frontend e UX
- **Task:** Renderização de Mapa da Loja (SVG)
- **Descrição:** Criar planta baixa da loja (`<section id="screen4">`) em vetor desenhado, contendo de corredores de 1 a 5, Entrada, e Caixas. Acionar mudança de classe SVG para destacar a rota para o corredor desejado via JS.
- **Critério de aceite:** Navegação pelo SPA exibe mapa vetorial de alta definição informando o percurso piscando dinamicamente com base na meta em `currentProduct.corredor`.
- **Dependências:** 3
- **Status sugerido:** Concluída

### 13. Implementação da intenção IR_PARA_MAPA
- **Épico:** Integração e IA
- **Task:** Modificação no fluxo comportamental do prompt
- **Descrição:** Atualizar instruções no `llm_service.py` impedindo o totem de dizer corredores em voz alta e adicionando reconhecimento da intenção `IR_PARA_MAPA`. A IA deve convidar e injetar a tag JSON para abrir o mapa via Frontend.
- **Critério de aceite:** A resposta verbal prioriza a descrição do produto e direciona o usuário para a tela de mapa quando há necessidade de apresentar a localização de forma visual/interativa. Ao identificar uma confirmação do usuário, a IA classifica a intenção como `IR_PARA_MAPA` e o frontend exibe o mapa visual com o item correspondente.
- **Dependências:** 7, 12
- **Status sugerido:** Concluída

### 14. Implementação do suporte multi-idioma
- **Épico:** Frontend e UX
- **Task:** Estrutura de Dicionário e UI de Seleção
- **Descrição:** Criar interface principal de início secundária (`<section id="screen-language">`) que permita chavear as strings do front entre PT/EN e injetar paramêtro HTTP de idioma nas chamadas de voz.
- **Critério de aceite:** Variável de ambiente selecionada em tempo real que afeta os labels da tela inteira, idioma de retorno do STT e do TTS (EdgeTTS Francisca vs versão em inglês).
- **Dependências:** 3, 7
- **Status sugerido:** Concluída

### 15. Implementação dos assets e áudios
- **Épico:** Arquitetura Base
- **Task:** Gestão de arquivos estáticos
- **Descrição:** Adicionar mapeamento estático na FastAPI (`app.mount()`) para servir cache de MP3 recém processados do EdgeTTS sob `/audios` em produção ou local.
- **Critério de aceite:** Geração dinâmica de áudios devolvida por URL válida para exibição e consumo em tempo real no Frontend.
- **Dependências:** 2, 7
- **Status sugerido:** Concluída

### 16. Revisão dos diagramas
- **Épico:** Documentação Técnica
- **Task:** Atualização arquitetural `diagrama-operacao.md`
- **Descrição:** Fazer um *as-built* documentando diagramas UML Mermaid (Sequência e Swimlane) com o fluxo de detecção de silêncio, SPA Front, STT->NLU->Banco->LLM->TTS, com `IR_PARA_MAPA` incluído.
- **Critério de aceite:** Arquivo `docs/diagramas/diagrama-operacao.md` versionado e exato ao código implementado na versão atual (MVP).
- **Dependências:** Todas até 15
- **Status sugerido:** Concluída

### 17. Atualização do PRD para a versão 3.1
- **Épico:** Documentação Técnica
- **Task:** Versionamento do PRD e fechamento do v1.0
- **Descrição:** Criar versão PRD 3.1 com correção de status de funcionalidades (Mapa, Idiomas) de fase v2.0 para "Implementado", e acréscimo de diretrizes do Prompt.
- **Critério de aceite:** `docs/prd/PRD-3.1.md` gerado.
- **Dependências:** 16
- **Status sugerido:** Concluída

### 18. Preparação da documentação final do TCC
- **Épico:** Documentação Acadêmica
- **Task:** Esboço do texto baseado nas tecnologias
- **Descrição:** Iniciar desenvolvimento dos capítulos "Desenvolvimento" e "Resultados", utilizando a estratégia técnica adotada, diagramas gerados e o rastreamento em `query.py` para provar a validade temporal do sistema (STT, LLM).
- **Critério de aceite:** Rascunho das teses de engenharia prontas na pasta `tcc/documento-principal/`.
- **Dependências:** 17
- **Status sugerido:** Em andamento

### 19. Entrada de texto como pendência técnica
- **Épico:** Frontend e UX
- **Task:** Integração total do text-input alternativo
- **Descrição:** Ajustar e conectar `<input type="text">` e tecla Enter na aba de chat enviando para o endpoint backend já pronto (`GET /query-text?q=`).
- **Critério de aceite:** Interface de digitação funcional de ponta-a-ponta, útil para quem não quer ou não pode usar voz no momento.
- **Dependências:** 10
- **Status sugerido:** A fazer

### 20. Alto contraste como pendência técnica
- **Épico:** Acessibilidade e Usabilidade
- **Task:** Botão interativo de UI Dark Theme
- **Descrição:** Incluir opção visual gráfica para chavear as classes CSS relativas ao modo de "Alto Contraste WCAG AA", salvando preferência localmente (`localStorage`).
- **Critério de aceite:** Tema responsivo de alto nível de contraste ativado com toque único na interface principal.
- **Dependências:** 3
- **Status sugerido:** A fazer

### 21. Exportação de logs de tempo em CSV como melhoria futura
- **Épico:** Documentação Acadêmica
- **Task:** Pipeline de logs de telemetria científica
- **Descrição:** Modificar print consoles espalhados nos arquivos `query.py` para injetar os micro-tempos em arquivo delimitado por vírgula (`telemetry.csv`) para tabulação estatística rápida para a Banca do TCC.
- **Critério de aceite:** Arquivo CSV guardado no backend compilando (timestamp_request, t_stt, t_nlu, t_tts, t_total).
- **Dependências:** 7
- **Status sugerido:** A fazer
