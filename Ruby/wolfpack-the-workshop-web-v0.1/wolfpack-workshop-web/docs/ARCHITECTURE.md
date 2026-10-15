# Arquitetura e implantação — WolfPack Workshop Web

## Etapa 1 / v0.1 (entregue)

```text
[Browser]
  |-- Homepage e catálogo de projetos [HTML/CSS]
  |-- Interface da campanha [JavaScript]
  |-- 12 lições carregadas como JSON
  |-- progresso local [localStorage]
  +-- Ruby WebAssembly [Worker dedicado]
        |-- compilação/carregamento sob demanda a partir de CDN
        |-- uma VM por caso de teste
        |-- entrada padrão em StringIO
        |-- saída capturada em StringIO
        +-- comparação de saída com o desafio
```

**Sem backend.** É intencional: podemos publicar uma primeira interface real com poucos custos e sem expor uma máquina executando diretamente código Ruby do visitante.

## O que é e não é virtualização

WebAssembly é uma tecnologia de execução portável dentro do navegador, mas **não equivale a uma VM Linux completa nem a isolamento rigoroso para código arbitrário**. O Worker apenas mantém a página responsiva e permite encerrar uma execução longa. Neste MVP, não há sistema de arquivos Linux persistente do jogador, shell, SSH, containers, VM remota, rede privada nem banco de dados.

## Etapa 2 / hospedagem segura de usuários (a projetar)

```text
[Browser em origem pública]
      |
      v
[API autenticada] ---- [PostgreSQL: usuários, progresso, cursos]
      |
      v
[Fila de execuções com cotas]
      |
      v
[Runner isolado, efêmero]
  - código de usuário sem privilégios
  - isolamento forte por sandbox/container/VM descartável
  - sem rede, sem credenciais ou volumes do host
  - filesystem somente-leitura + tmpfs efêmero
  - cotas CPU, memória, PIDs, disco, output e tempo
  - perfil seccomp/AppArmor e sem novas capacidades
  - egress restrito e observabilidade dos limites
      |
      v
[Saída filtrada e avaliada]
```

Notas para endurecimento antes de uma versão pública:

- Nunca execute código submetido diretamente no processo HTTP/API.
- Trate os programas como dados hostis e verifique pontos de exfiltração e consumo de recursos.
- Proíba ponte JavaScript que acesse origin/sessões privilegiadas em qualquer sandbox de browser para código de terceiros.
- Separe por origem sem cookies e audite o carregamento de bibliotecas externas; adote dependências fixadas e preferencialmente hospedadas sob controle após revisão.
- Adicione login, limites por IP/usuário, proteção contra abuso, logs mínimos com privacidade e retenção explícita.
- Testes funcionais do browser e cenários de carga antes de divulgar execução segura a usuários externos.

## Próximas aplicações no catálogo

Os cards ARES (C/Redes), ARGUS (Python/observação), RAVEN (Ruby/DSL), CERBERUS (orquestração), HTTP Auditor e Crypto Lab são **informativos**; ainda não foram implementados como interfaces web nesta entrega. Cada uma pode virar uma aplicação isolada, integrada ao portal por rota, link ou microfrontend depois de revisão de escopo e segurança.
