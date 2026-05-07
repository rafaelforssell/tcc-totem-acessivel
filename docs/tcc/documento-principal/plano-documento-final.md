# Plano de Evolução do Documento Final (TCC)

Este plano foi desenvolvido a partir do cruzamento entre o **Manual de TCC da UNISANTA** (`manual_tcc.pdf`), o esboço atual (`tcc-totem-acessivel-v01.pdf`), a documentação do projeto (PRD 3.1 e OpenProject) e a base de código do repositório.

---

## 1. Resumo das exigências identificadas no manual do TCC
De acordo com o manual, um trabalho acadêmico (teórico-prático) deve obrigatoriamente seguir a estrutura:
- **Pré-texto:** Capa, Folha de rosto, Folha de Aprovação, Resumo (sem numeração de capítulo) e Sumário.
- **Texto:** 
  - *Introdução* (englobando definição do tema, justificativa e objetivos).
  - *Desenvolvimento*, subdividido em: Fundamentação Teórica, Material e Métodos, Resultados e Discussão.
  - *Conclusões/Sugestões*.
- **Pós-texto:** Referências.
- **Formatação:** A numeração começa a ser impressa apenas a partir da Introdução. Títulos de primeiro nível em maiúsculas e negrito.

## 2. Comparação entre o manual e o documento atual (v01)
O documento atual `tcc-totem-acessivel-v01.pdf` apresenta erros estruturais em relação ao manual:
- **Numeração incorreta do Pré-texto:** O *Resumo* está numerado como capítulo "1".
- **Fragmentação da Introdução:** A *Introdução*, *Justificativa* e *Objetivos* estão como capítulos independentes (2, 3, 4 e 5), contrariando a recomendação de mantê-los contidos na Introdução.
- **Ausência de Resultados:** O texto para na seção de Arquitetura. Por ser um trabalho prático, falta apresentar formalmente os "Resultados e Discussão".
- **Nomenclatura:** As seções 7 (Metodologia) e 8 (Arquitetura) devem ser unificadas ou reorganizadas dentro de "Material e Métodos".

## 3. Estrutura sugerida para o documento final
Abaixo, a nova estrutura de sumário alinhada à ABNT e ao Manual:

> [Elementos Pré-Textuais não numerados]
> Resumo
> Sumário
> 
> **1 INTRODUÇÃO**
> 1.1 Justificativa
> 1.2 Objetivos (Geral e Específicos)
>
> **2 REVISÃO DA LITERATURA** (ou Fundamentação Teórica)
> 2.1 Inteligência Artificial e Modelos de Linguagem
> 2.2 Tecnologias Assistivas e Acessibilidade no Varejo
> 
> **3 MATERIAL E MÉTODOS**
> 3.1 Arquitetura do Sistema Integrado
> 3.2 Desenvolvimento do Frontend (Interface e Captura de Áudio)
> 3.3 Desenvolvimento do Backend e Processamento de IA
> 3.4 Procedimentos de Teste e Mensuração de Desempenho
>
> **4 RESULTADOS E DISCUSSÃO**
> 4.1 Avaliação do Pipeline de Inteligência Artificial
> 4.2 Análise de Interface, Mapa Interativo e Acessibilidade
> 4.3 Desempenho Computacional e Tempos de Resposta
>
> **5 CONCLUSÕES**
> 5.1 Trabalhos Futuros
> 
> **REFERÊNCIAS**

## 4. O que deve ser escrito ou revisado em cada capítulo
- **Introdução:** Mesclar os capítulos antigos (1 a 5).
- **Revisão da Literatura:** Focar no estudo sobre LLaMA 3.3, Whisper e as barreiras que pessoas com Deficiência Visual enfrentam no varejo físico.
- **Material e Métodos:** Descrever o processo de engenharia, detalhando as ferramentas e o código construído.
- **Resultados e Discussão:** Este é o capítulo mais importante a ser escrito agora. Apresentar os dados de execução e discutir as escolhas arquiteturais da UI.
- **Conclusões:** Sintetizar o alcance dos objetivos e propor melhorias.

## 5. Informações do repositório a serem aproveitadas (por capítulo)
- **Material e Métodos:** 
  - Explicar a organização do `backend/main.py` e rotas.
  - Explicar a lógica de fallback do SQLite (AND seguido de OR).
  - Citar a `Web Audio API` localizada no `frontend/index.html` usada para captura e interrupção.
- **Resultados:** Os temporizadores (`time.time()`) existentes em `backend/routes/query.py` que marcam o início e o fim de cada etapa (`STT`, `IA`, `TTS`).

## 6. Informações do PRD 3.1 a serem aproveitadas
- A Tabela de Usuários-Alvo (inserir na Introdução/Justificativa).
- O Fluxograma Mermaid (STT -> NLU -> Banco -> LLM -> TTS) (inserir em Material e Métodos).
- A **Estratégia de Engajamento e Navegação**, na qual a resposta verbal prioriza a descrição do produto e direciona o usuário para a interface visual do mapa quando há necessidade de apresentar a localização de forma mais clara e interativa (Excelente para a Discussão de UX).

## 7. Uso do OpenProject para demonstrar gestão
No capítulo de Material e Métodos, pode ser criada uma subseção "Gestão do Desenvolvimento". As informações organizadas em `openproject-tasks.md` (separação por Épicos como *Integração e IA*, *Frontend e UX*) devem ser usadas para mostrar à banca que o projeto não foi caótico, e que funcionalidades de v2.0 (Mapa e Multi-idioma) foram antecipadas com sucesso.

## 8. Pontos técnicos com destaque acadêmico
Para garantir uma boa nota, o documento deve enfatizar:
1. **Detecção Autônoma de Silêncio:** O uso da Web Audio API calculando o volume acústico em tempo real para interromper a gravação sem depender de cliques físicos (Acessibilidade essencial para pessoas cegas e com problemas motores).
2. **Separação de NLU:** A arquitetura inteligente de dividir o LLaMA em dois papéis: um extrator *Analítico* (gerando JSON da intenção) e um gerador *Sintético* (criando o áudio final). Isso controla a alucinação e garante buscas seguras.
3. **Mapeamento SVG Dinâmico:** A lógica do JavaScript de alterar os seletores CSS do mapa vetorial (`screen4`) iluminando corredores baseados na intenção `IR_PARA_MAPA`.

## 9. Pendências que precisam ser alinhadas com o grupo
Antes de fechar o documento, o grupo deve:
- Decidir se as pendências técnicas de UI (Entrada de Texto e Alto Contraste) serão programadas para a banca final ou se irão para "Trabalhos Futuros".
- Exportar os logs de latência do FastAPI (necessário fazer requisições teste e tabular os tempos de resposta).
- Validar se haverá aplicação do questionário SUS (System Usability Scale) com um voluntário real.

## 10. Ordem recomendada de trabalho
1. **Adequação estrutural:** Abrir o `.docx/.tex` atual e arrumar a formatação dos títulos (Introdução passa a abrigar Objetivos e Justificativa).
2. **Material e Métodos:** Escrever o capítulo 3 focando no pipeline consolidado.
3. **Geração de Dados:** Rodar a aplicação algumas vezes, pegar os tempos do terminal e criar gráficos estatísticos.
4. **Resultados:** Escrever a Discussão baseada nos dados do passo anterior.
5. **Introdução e Conclusão:** Ajuste fino e redação do resumo final.
