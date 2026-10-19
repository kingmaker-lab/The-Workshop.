# 🐺 The Workshop

> **Build. Break. Understand. Rebuild.**

**The Workshop** é meu laboratório pessoal de pesquisa, desenvolvimento e experimentação.

Este repositório reúne projetos, estudos, ferramentas, provas de conceito e experimentos construídos ao longo do tempo em áreas como engenharia de software, cybersecurity, programação de baixo nível, redes, criptografia, automação, inteligência artificial, matemática aplicada e computação.

Não existe uma única stack.

Não existe um único produto.

Existe uma bancada.

A ideia é simples: transformar estudo em experimento, experimento em código e código em conhecimento reutilizável.

---

## ⚙️ Filosofia

Nem tudo aqui nasceu para se tornar um produto completo.

Alguns projetos são ferramentas.

Outros são estudos de arquitetura.

Alguns existem para explorar uma linguagem, algoritmo, protocolo ou conceito.

Outros provavelmente crescerão muito além da ideia original.

O objetivo é manter um registro prático da evolução técnica:

```text
IDEA
  │
  ▼
RESEARCH
  │
  ▼
PROTOTYPE
  │
  ▼
BUILD
  │
  ▼
BREAK
  │
  ▼
UNDERSTAND
  │
  ▼
REBUILD
```

---

# 🔬 Areas of Research

O Workshop não está limitado a uma tecnologia ou domínio específico.

### Systems Engineering

- C / C++
- programação de baixo nível
- gerenciamento de memória
- sockets
- protocolos
- concorrência
- arquitetura de sistemas

### Cybersecurity

- network security
- threat hunting
- detection engineering
- application security
- malware analysis
- reverse engineering
- security research
- observabilidade

### Cryptography

- criptografia aplicada
- implementação de primitivas
- protocolos criptográficos
- análise experimental
- estudos acadêmicos

### Mathematics & Computational Research

- métodos estocásticos
- processos aleatórios
- Monte Carlo
- cadeias de Markov
- inferência Bayesiana
- probabilidade
- estatística
- modelagem computacional

### Artificial Intelligence

- machine learning
- detecção de anomalias
- análise comportamental
- LLM security
- automação inteligente
- experimentação com modelos

### Networking

- TCP/IP
- análise de protocolos
- packet processing
- network monitoring
- sistemas distribuídos

### Hardware & Embedded

- Arduino
- sensores
- sistemas embarcados
- comunicação hardware/software
- experimentação eletrônica

### Automation & Web

- Python
- Ruby
- JavaScript
- APIs
- WebApps
- ferramentas internas
- automação de workflows

---

# 🧪 Projects

Alguns dos projetos e experimentos atualmente presentes no Workshop:

## ARES

Servidor HTTP/1.1 desenvolvido em **C** sobre sockets POSIX.

**Experimento v0.1 — TCP Foundation:** [código, testes e documentação](ares/tcp-foundation/README.md) · [página no Workshop Labs](https://workshop-labs.pages.dev/projects/ares/tcp-foundation/). O laboratório TCP funciona somente em localhost; a implementação HTTP do diretório raiz permanece preservada e é um protótipo distinto.

**Experimento v0.2 — HTTP Parser:** [código, testes e documentação](ares/http-parser/README.md) · [página no Workshop Labs](https://workshop-labs.pages.dev/projects/ares/http-parser/). Parser de cabeçalhos HTTP/1.x em C17, com alimentação incremental, limites explícitos e validações; funciona offline, sem servidor de rede.

**Experimento v0.3 — Responses & Routing:** [código e testes E2E](ares/http-server/README.md) · [página no Workshop Labs](https://workshop-labs.pages.dev/projects/ares/responses-routing/). Agora há servidor C integrado: TCP → Parser v0.2 → roteador → resposta HTTP. Executa **apenas em 127.0.0.1**. `make run-ares` aponta para ele.

**Security Release Gate obrigatório:** [checklist permanente de segurança](docs/SECURITY_RELEASE_GATE.md). A cada implementação/deploy são exigidos testes do código, revisão dos headers e rotas do site, CI e registro de riscos. Execute `make check-security`.

Explora conceitos como:

- sockets;
- parsing HTTP;
- gerenciamento de memória;
- validação de entrada;
- segurança de filesystem;
- programação de sistemas.

---

## ARGUS

Motor defensivo de **Threat Hunting e correlação de eventos em Python**.

Explora:

- normalização de eventos;
- correlação temporal;
- SQLite;
- risk scoring;
- detection engineering;
- análise comportamental.

---

## RAVEN

Motor de regras temporais e DSL desenvolvido em **Ruby**.

Explora:

- metaprogramação;
- DSLs;
- regras declarativas;
- janelas temporais;
- agrupamento de eventos;
- detection engineering.

---

## WolfHunter

Conjunto experimental de ferramentas e interfaces voltadas para análise, automação e pesquisa em segurança.

O projeto evolui conforme novas necessidades aparecem dentro do laboratório.

---

## Ouroboros

Área experimental dedicada a estudos, protótipos e pesquisas que não necessariamente pertencem a um único domínio do Workshop.

---

# 📚 Research

Além dos projetos de software, o Workshop também funciona como repositório para estudos técnicos e experimentação científica.

A intenção é que pesquisas sejam acompanhadas, sempre que possível, por implementações reproduzíveis.

Exemplo:

```text
research/
│
├── stochastic-methods/
│   ├── monte-carlo/
│   ├── markov-chains/
│   ├── random-walks/
│   ├── poisson-process/
│   └── bayesian-inference/
│
├── cryptography/
├── network-science/
├── artificial-intelligence/
└── security-research/
```

A filosofia é:

```text
Theory → Implementation → Experiment → Observation
```

---

# 🧰 Technology

A stack do Workshop é deliberadamente heterogênea.

Cada problema deve ser resolvido com a ferramenta adequada, e não adaptado artificialmente a uma linguagem específica.

Atualmente podem aparecer por aqui:

```text
C
C++
Python
Ruby
JavaScript
HTML / CSS
Shell
SQL
Assembly
Java
Kotlin
Arduino
```

E essa lista provavelmente vai crescer.

> **Use whatever the problem demands.**

---

# 🏗️ Repository Philosophy

O Workshop funciona mais como um **monorepo de pesquisa pessoal** do que como uma aplicação tradicional.

Por isso, diferentes diretórios podem possuir:

- arquitetura própria;
- dependências próprias;
- documentação própria;
- linguagens diferentes;
- níveis diferentes de maturidade.

Projetos maiores devem possuir seus próprios `README.md`.

O README raiz descreve **a oficina**.

Os READMEs internos descrevem **as máquinas construídas nela**.

---

# 🚧 Project Status

Os projetos podem passar por diferentes estados:

```text
[ IDEA ]         conceito ou pesquisa inicial

[ EXPERIMENT ]   prova de conceito

[ BUILDING ]     desenvolvimento ativo

[ STABLE ]       implementação funcional

[ ARCHIVED ]     estudo preservado, sem desenvolvimento ativo
```

Nem todo experimento precisa chegar a `STABLE`.

Fracassos também produzem conhecimento.

---

# 🐺 The Workshop

Este repositório não pretende representar uma stack específica.

Ele representa um processo.

Um lugar para experimentar linguagens, sistemas, matemática, segurança e ideias sem exigir que cada tentativa se transforme em produto.

Algumas coisas vão funcionar.

Algumas vão quebrar.

Algumas serão abandonadas.

E algumas provavelmente vão crescer muito além do planejado.

**That's what workshops are for.**

---

`Build. Break. Understand. Rebuild.`