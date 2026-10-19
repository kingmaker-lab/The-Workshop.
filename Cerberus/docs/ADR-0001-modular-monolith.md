# ADR 0001 — Iniciar estudo por monólito modular

- **Status:** hipótese educacional; decisão final pendente de medição.
- **Data:** 2026-10-19
- **Contexto:** sistema hipotético de reservas (Catálogo, Reservas, Notificações), equipe de três desenvolvedores, orçamento limitado e volume inicial baixo.

## Opções

1. **Monólito modular:** deploy único, contratos internos explícitos e persistência organizada por limites de domínio.
2. **Microsserviços:** deploys separados, comunicação pela rede, maior independência potencial e maior complexidade operacional.

## Hipótese preferida

Explorar primeiro o monólito modular para reduzir o custo operacional durante a fase inicial, sem impedir uma extração futura de serviços bem delimitados.

## Consequências esperadas

- Simplicidade de deploy, observabilidade e testes integrados.
- Disciplina necessária para preservar fronteiras; sem isso, o monólito degrada.
- Ampliação de escala e independência de times poderá motivar outra arquitetura.

## Plano de validação

Medir p95 de latência sob mesma carga, taxa de falha, custo de deploy e esforço de manutenção. Registrar resultados, condições de teste e limitações. Reavaliar a opção quando os requisitos de escala, confiabilidade ou autonomia operacional mudarem.

**Atenção:** nenhuma métrica foi coletada até esta versão. A preferência é uma hipótese, não um resultado experimental.
