# Geração dos dados sintéticos de oferta e recompensa

Este relatório documenta como `data/synthetic_enrichment/offer_catalog.csv`,
`data/synthetic_enrichment/offer_events.csv` e
`data/synthetic_enrichment/delayed_rewards.csv` foram gerados a partir de
`build_offer_catalog`/`save_offer_catalog` (`src/bandit_platform/synthetic/offer_catalog.py`)
e `simulate_offer_events`/`simulate_delayed_rewards`
(`src/bandit_platform/synthetic/events.py`), rodados uma única vez contra a base
real e completa da Etapa 1.

## Processo

A entrada é `data/processed/bank_marketing.csv`, a camada processada da Etapa 1
(**41.188 linhas**, 21 colunas, `target` real derivado de `y`, sem `duration` por
vazamento — ver `reports/data-quality.md`). A partir dela geramos três arquivos:

- `offer_catalog.csv`: os 6 braços/ofertas disponíveis (estático, não depende dos
  dados de clientes).
- `offer_events.csv`: um evento sintético por linha de `bank_marketing.csv`
  (**41.188 eventos**, um a um) — qual braço foi mostrado a cada cliente e se
  houve engajamento imediato.
- `delayed_rewards.csv`: a conversão final, só para os eventos que engajaram, com
  atraso simulado de 1 a 14 dias.

A separação física de `data/kaggle/` (dados brutos baixados do Kaggle,
`data/kaggle/raw/` + `data/kaggle/dataset_manifest.json`), `data/processed/`
(camada limpa da Etapa 1) e `data/synthetic_enrichment/` (esta etapa) é
intencional: mantém claro que o dataset real do cliente/campanha é uma coisa, e o
enriquecimento sintético de ofertas/recompensas de bandit é outra, construída por
cima — sem misturar proveniência real e simulada no mesmo diretório.

## Catálogo de braços

`offer_catalog.csv` tem 6 braços, cada um com `offer_id`, `name`, `channel`,
`product_type`, `description` e `policy_doc` (aponta para um documento fictício em
`data/synthetic_enrichment/policy_docs/`):

| offer_id | canal | product_type |
|---|---|---|
| cdb_12m | email | cdb |
| cdb_24m | call | cdb |
| poupanca_programada | sms | poupanca |
| reserva_emergencia | push | consultivo |
| fundo_liquidez_diaria | email | fundo |
| taxa_promocional | sms | cdb |

Nenhuma coluna deste arquivo carrega um parâmetro de "efetividade real" do braço.
Esses parâmetros existem, mas ficam em `ARM_CONVERSION_EFFECT` dentro de
`src/bandit_platform/synthetic/events.py` (junto de `CHANNEL_ENGAGEMENT_RATE`, a
taxa-base de engajamento por canal) — são o *ground truth* interno do ambiente de
simulação, o equivalente à função de recompensa "verdadeira" que qualquer política
de bandit deveria descobrir por tentativa e erro. Documentamos aqui por
transparência, mas eles nunca devem ser expostos como feature a uma política/modelo
em avaliação na Etapa 3: se a política "enxergasse" esse valor, deixaria de ser um
problema de bandit e viraria uma tabela de consulta.

## Contexto da decisão

Cada linha de `offer_events.csv` tem `client_context_id`, que é exatamente o
índice (posição, base 0) da linha correspondente em
`data/processed/bank_marketing.csv` no momento em que o processed foi lido. Ele
varia de 0 a 41.187, com **41.188 valores únicos** — uma correspondência 1:1 com
as 41.188 linhas do processed. Isso permite recuperar o contexto completo do
cliente (idade, profissão, indicadores macroeconômicos etc.) fazendo um `join`/
`loc` por esse índice, sem duplicar as 21 colunas originais dentro do arquivo
sintético — `offer_events.csv` só guarda `event_id`, `client_context_id`, `arm_id`,
`channel`, `logging_policy` e `intermediate_reward`.

## Recompensa intermediária vs. atrasada

- **`intermediate_reward`** (engajamento): resolvido no próprio momento do evento,
  amostrado como Bernoulli com taxa de sucesso dada por `CHANNEL_ENGAGEMENT_RATE`
  do canal do braço sorteado (`email` 0,35 / `sms` 0,55 / `push` 0,45 / `call`
  0,65, valores de design). Na execução real, a taxa de engajamento observada
  agregada foi **48,64%** (0,4864), e por canal ficou muito próxima do parâmetro
  de design, como esperado para uma amostra grande: `call` 65,81%, `sms` 55,31%,
  `push` 45,50%, `email` 35,04%.
- **`final_reward`** (conversão): só existe em `delayed_rewards.csv` para eventos
  com `intermediate_reward == 1` (engajados) — dos 41.188 eventos, **20.032**
  engajaram e por isso têm linha em `delayed_rewards.csv`. O atraso
  (`delay_days`) é sorteado uniformemente entre 1 e 14 dias
  (`rng.integers(1, max_delay_days + 1)`, `max_delay_days=14`) — horizonte de até
  duas semanas entre engajamento e conversão observada, com média observada de
  7,51 dias e mediana de 7 dias no lote gerado. A taxa de conversão final entre os
  engajados foi **14,43%** (0,1443).

## Sementes

Duas sementes fixas e independentes controlam a geração, cada uma passada
explicitamente como argumento `seed`:

- **`20260707`** para `simulate_offer_events` (sorteio de braço por cliente via
  `rng.choice` e Bernoulli de `intermediate_reward`).
- **`97531`** para `simulate_delayed_rewards` (Bernoulli de `final_reward` e
  sorteio uniforme de `delay_days`).

Ambas usam `numpy.random.default_rng(seed)`, um gerador determinístico: rodar o
Step 1 de novo com essas mesmas sementes, sobre o mesmo `bank_marketing.csv`,
reproduz exatamente os mesmos três arquivos, byte a byte. Isso foi confirmado
explicitamente (ver Step 3 — reprodutibilidade — nenhuma diferença entre a
geração original e uma segunda geração independente).

## Hipóteses

A propensão-base de conversão de cada cliente engajado vem do `target` real da
Etapa 1 (0 ou 1, derivado de `y`), suavizada por `base_propensity = target * 0.8 +
0.05` antes de multiplicar pelo efeito do braço (`ARM_CONVERSION_EFFECT`,
limitado a `[0, 1]` no final). Essa suavização evita que a simulação seja
puramente determinística 0/1 (cliente que nunca converteria no mundo real vs.
cliente que sempre converteria) — em vez disso, todo cliente tem uma propensão
residual de 0,05 e um teto de 0,85 antes do efeito do braço, preservando o sinal
real do `target` (clientes que de fato converteram na campanha original tendem a
converter mais na simulação) sem eliminar a variância. É uma simplificação
deliberada para ter um ambiente de simulação com sinal real e ruído controlado,
não uma alegação de que qualquer braço específico teria esse efeito de conversão
em produção.

## Limitações e riscos

- **Atribuição de braço é aleatória uniforme**: `simulate_offer_events` sorteia o
  braço de cada cliente com `rng.choice(offer_ids, size=n)` sem pesos, registrado
  como `logging_policy = "random_uniform_v0"` (valor único e constante nas
  41.188 linhas geradas). Isso simula uma política de "logging" exploratória, não
  uma política de negócio real — qualquer viés de atribuição real (ex.: gerentes
  oferecendo CDB de prazo maior para clientes de maior renda) não está presente.
- **Os documentos de política comercial em `policy_docs/` são fictícios**,
  escritos para dar contexto textual às ofertas, não representam política de
  crédito/investimento real de nenhuma instituição.
- **O efeito de cada braço (`ARM_CONVERSION_EFFECT`) é arbitrário**, escolhido
  para criar diferenciação suficiente entre braços (de 0,75 a 1,30) para que, na
  Etapa 3, seja possível comparar politicas de bandit e observar que algumas
  aprendem a favorecer os braços de maior efeito — não é uma estimativa de
  mercado real. Como evidência dessa arbitrariedade e do ruído de amostragem:
  observado entre os engajados, `taxa_promocional` teve a maior taxa de conversão
  final (16,50%), levemente acima de `cdb_24m` (16,34%) mesmo `cdb_24m` tendo o
  maior multiplicador de design (1,30 vs. 1,20) — a ordem de efeito de design é
  aproximada pela amostra, mas não replicada exatamente linha a linha, porque a
  propensão-base de cada cliente também varia.
- Como a taxa de conversão real de campanha é rara (~11,3% na base original,
  ver `reports/data-quality.md`), a taxa de conversão final simulada entre os
  **engajados** (14,43%) não deve ser comparada diretamente com a taxa de
  conversão da campanha original — são recompensas de ambientes diferentes
  (bandit sintético vs. campanha telefônica real).
