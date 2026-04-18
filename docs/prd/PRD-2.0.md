# PRD 2.0 — Totem de Autoatendimento com Recursos de Acessibilidade

## 1. Visão do Produto
O projeto consiste em um totem de autoatendimento acessível, projetado para auxiliar usuários na busca, identificação e localização de produtos em lojas físicas, com foco especial em acessibilidade para pessoas com deficiência visual.

A solução pretende oferecer uma experiência de uso simples, inclusiva e funcional, combinando interface acessível, processamento inteligente das consultas e retorno claro ao usuário por meios visuais e sonoros.

Este documento descreve o produto sob a ótica de problema, proposta de valor, escopo, funcionalidades, requisitos e critérios de evolução.

---

## 2. Contexto do Problema
Em ambientes varejistas, a localização de produtos ainda depende com frequência de atendimento humano, leitura visual de placas, organização física da loja e familiaridade prévia do cliente com o espaço.

Esse cenário cria barreiras para diferentes perfis de usuários, principalmente pessoas com deficiência visual, que podem enfrentar dificuldades para encontrar produtos com autonomia, segurança e agilidade.

Além da limitação de acessibilidade, esse tipo de dependência também pode gerar:
- aumento do tempo de atendimento;
- repetição de dúvidas operacionais simples;
- sobrecarga de funcionários em consultas básicas;
- experiência de compra menos fluida e menos inclusiva.

O produto surge como resposta a esse contexto, propondo uma solução acessível de autoatendimento para apoio à navegação informacional dentro da loja.

---

## 3. Objetivo do Produto
Desenvolver um sistema de autoatendimento acessível que permita ao usuário consultar produtos de maneira simples, recebendo como resposta informações claras sobre o item solicitado, sua disponibilidade lógica no sistema e sua localização dentro do ambiente da loja.

O objetivo central é transformar uma tarefa que hoje depende fortemente de assistência humana em uma interação mais autônoma, inclusiva e eficiente.

---

## 4. Público-Alvo
### 4.1 Público principal
- Pessoas com deficiência visual
- Usuários com dificuldade de navegação visual no ambiente
- Clientes que desejam localizar produtos com mais rapidez e autonomia

### 4.2 Público secundário
- Lojas e estabelecimentos que desejam ampliar acessibilidade
- Equipes operacionais que podem se beneficiar da redução de consultas repetitivas
- Ambientes comerciais que buscam melhorar experiência do cliente com apoio tecnológico

---

## 5. Proposta de Valor
O produto busca entregar valor em quatro frentes principais:

### 5.1 Acessibilidade
Permitir que usuários realizem consultas de forma mais inclusiva, com retorno em áudio e interface acessível.

### 5.2 Autonomia
Reduzir a dependência de atendentes para localização e identificação de produtos.

### 5.3 Eficiência
Tornar mais rápida a obtenção de informações sobre itens dentro da loja.

### 5.4 Evolução tecnológica
Estruturar uma solução modular e evolutiva, capaz de crescer em inteligência, cobertura e robustez ao longo do desenvolvimento.

---

## 6. Escopo do MVP
A primeira versão funcional do produto deve contemplar o fluxo principal de consulta e resposta, demonstrando viabilidade técnica e utilidade prática.

### 6.1 O que entra no MVP
- interface inicial de interação com o usuário;
- recebimento de consulta;
- interpretação da solicitação;
- busca em base local de produtos;
- organização da resposta;
- retorno da resposta em tela;
- retorno da resposta em áudio;
- funcionamento local;
- estrutura básica de dados do catálogo;
- validação do fluxo principal do sistema.

### 6.2 O que fica fora do MVP
- integração com sistemas externos em tempo real;
- gestão completa de estoque real da loja;
- analytics avançado de uso;
- múltiplos perfis administrativos;
- recomendação complexa baseada em comportamento;
- cobertura de cenários comerciais amplos e não controlados.

---

## 7. Funcionalidades Principais
### 7.1 Consulta de produto
O sistema deve permitir que o usuário consulte um item desejado por meio da interface disponível no totem.

### 7.2 Interpretação da solicitação
O sistema deve interpretar a intenção do usuário a partir da entrada recebida e transformá-la em consulta processável.

### 7.3 Busca de informações
O sistema deve localizar informações relevantes em sua base de dados local, considerando nome, categoria, atributos ou proximidade semântica da solicitação.

### 7.4 Geração de resposta compreensível
O sistema deve organizar uma resposta clara, objetiva e adequada ao contexto da consulta.

### 7.5 Resposta multimodal
A resposta deve ser apresentada:
- visualmente, na interface do totem;
- auditivamente, por saída de áudio.

### 7.6 Sugestão de alternativas
Quando o item solicitado não for encontrado de forma exata, o sistema deve ser capaz de sugerir alternativas relevantes.

### 7.7 Organização modular
A solução deve permitir evolução futura dos módulos de entrada, busca, interpretação, resposta e dados sem depender de uma única implementação fixa desde o início.

---

## 8. Jornada Principal do Usuário
## 8.1 Fluxo principal
1. O usuário inicia a interação com o totem.
2. O sistema recebe a solicitação.
3. O sistema interpreta a consulta.
4. O sistema realiza a busca das informações relevantes.
5. O sistema organiza a resposta final.
6. O sistema apresenta a resposta em tela e áudio.
7. O usuário utiliza a informação recebida para localizar o produto.

### 8.2 Fluxos alternativos esperados
- produto não encontrado;
- produto encontrado com baixa precisão;
- múltiplos resultados possíveis;
- necessidade de sugerir item semelhante;
- falha na entrada ou necessidade de repetição da consulta.

---

## 9. Requisitos Funcionais
- O sistema deve permitir ao usuário iniciar uma consulta de produto.
- O sistema deve processar a entrada recebida e extrair a intenção principal da consulta.
- O sistema deve consultar uma base local de dados de produtos.
- O sistema deve retornar informações relevantes sobre o item solicitado.
- O sistema deve informar a localização do produto dentro do contexto modelado da loja.
- O sistema deve sugerir alternativas quando o item exato não for encontrado.
- O sistema deve apresentar a resposta em formato visual.
- O sistema deve apresentar a resposta em formato sonoro.
- O sistema deve permitir evolução futura dos componentes sem necessidade de reestruturação total do projeto.
- O sistema deve permitir testes funcionais do fluxo completo.

---

## 10. Requisitos Não Funcionais
### 10.1 Acessibilidade
- A solução deve priorizar acessibilidade para pessoas com deficiência visual.
- A interface deve ser simples, clara e intuitiva.
- A saída de resposta deve ser compreensível.

### 10.2 Desempenho
- O sistema deve apresentar tempo de resposta adequado ao contexto de uso.
- O fluxo principal deve ocorrer sem travamentos críticos.

### 10.3 Operação local
- O sistema deve ser capaz de operar localmente dentro do escopo do protótipo.
- O funcionamento não deve depender obrigatoriamente de conexão contínua com internet para a demonstração principal.

### 10.4 Manutenibilidade
- A estrutura deve ser modular.
- A organização do projeto deve facilitar documentação, manutenção e evolução.

### 10.5 Escalabilidade conceitual
- A arquitetura deve permitir expansão futura do número de produtos, das regras de interpretação e da robustez do sistema.

---

## 11. Estrutura de Alto Nível do Produto
O produto pode ser compreendido em cinco blocos principais:

### 11.1 Camada de interação
Responsável pela interface do totem e pelo ponto de contato com o usuário.

### 11.2 Camada de entrada
Responsável por receber a solicitação do usuário e encaminhá-la para processamento.

### 11.3 Camada de processamento
Responsável por interpretar a consulta, buscar informações relevantes, aplicar contexto e estruturar a resposta.

### 11.4 Camada de dados
Responsável por armazenar e disponibilizar informações dos produtos e dados necessários para a lógica do sistema.

### 11.5 Camada de saída
Responsável por apresentar a resposta final de maneira visual e sonora.

---

## 12. Critérios de Sucesso do MVP
O MVP será considerado bem-sucedido se conseguir demonstrar, de forma estável e compreensível, o fluxo principal da solução.

### Indicadores de sucesso
- o usuário consegue iniciar a interação sem dificuldade relevante;
- o sistema interpreta consultas básicas com consistência;
- o sistema localiza produtos cadastrados na base;
- o sistema consegue responder com clareza;
- o fluxo completo de consulta e resposta funciona no protótipo;
- a experiência demonstra potencial real de acessibilidade e utilidade prática.

---

## 13. Riscos e Restrições
### 13.1 Riscos
- mudanças nas ferramentas adotadas ao longo do projeto;
- dificuldade de integração entre módulos;
- limitações de precisão em consultas ambíguas;
- necessidade de ajustes finos de acessibilidade;
- complexidade de validação prática em ambiente próximo do real.

### 13.2 Restrições
- tempo acadêmico de desenvolvimento;
- escopo controlado do protótipo;
- dependência de integração entre frentes técnicas;
- limitação inicial da base de produtos;
- necessidade de priorização para entrega incremental.

---

## 14. Premissas do Projeto
- O projeto será desenvolvido de forma incremental.
- O repositório servirá como base de documentação e evolução técnica.
- O protótipo inicial deve priorizar demonstração funcional e clareza de proposta.
- As ferramentas específicas podem evoluir ao longo do projeto, desde que a arquitetura conceitual permaneça coerente.
- A documentação deve acompanhar o desenvolvimento técnico.

---

## 15. Evolução Futura
Em versões futuras, a solução poderá evoluir para:
- ampliação da base de produtos;
- melhoria da interface de interação;
- maior robustez na interpretação das consultas;
- refinamento da camada de contexto;
- expansão de cenários de acessibilidade;
- integração com outras bases e módulos;
- melhoria da experiência de navegação dentro do ambiente.

---

## 16. Próximos Passos
- consolidar a versão 2.0 do PRD no repositório;
- alinhar o escopo com o grupo;
- conectar o PRD com a documentação principal do TCC;
- detalhar a arquitetura técnica em diagramas;
- organizar a documentação das próximas etapas de implementação;
- acompanhar a evolução do backend, frontend e camada de dados de forma sincronizada.

---

## 17. Status do Documento
Versão: 2.0  
Natureza: Documento em evolução  
Objetivo atual: Consolidar visão de produto, escopo inicial e base de desenvolvimento do projeto
