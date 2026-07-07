# Diretrizes Gerais de Suitability (sintético/fictício)

Este documento é fictício, criado para fins de demonstração do Datathon 7MLET,
e complementa as políticas por produto (`policy_*.md`).

## Princípios gerais

1. Nenhuma oferta deve ser exibida mais de uma vez ao mesmo cliente dentro da
   mesma campanha se a tentativa anterior não gerou engajamento
   (`intermediate_reward = 0`).
2. Clientes com `default = yes` são inelegíveis para qualquer oferta de crédito
   ou investimento (CDB, Fundo) — apenas a mensagem consultiva pode ser
   exibida a esse segmento.
3. A exploração de braços (bandit) não deve concentrar mais de 60% do tráfego
   em um único braço nas primeiras 1000 decisões de uma campanha nova — ver
   análise de exploração na Etapa 4.
4. Toda decisão automatizada deve ficar registrada com "reason code" e versão
   da política aplicada (ver Etapa 5), para auditoria humana posterior.

## Base legal e finalidade

Tratamento de dados aqui descrito é fictício e não envolve dados reais de
clientes — ver `docs/lgpd-plan.md` (Etapa 8) para o tratamento formal de base
legal, finalidade e minimização quando esse documento existir.
