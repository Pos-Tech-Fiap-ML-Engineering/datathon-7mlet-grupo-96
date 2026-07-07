# Avaliação offline: golden set, sensibilidade e fairness

Este documento registra os números brutos observados ao rodar o golden set
contra as três políticas (com a guarda de suitability), uma análise de
sensibilidade de hiperparâmetros e uma análise de fairness de exposição entre
segmentos de `job`. O texto narrativo completo com interpretação será escrito
em seguida; por ora, os números abaixo são a saída literal dos comandos
executados contra os dados reais das Etapas 1-2.

## Passo 1: golden set (22 casos) contra as três políticas guardadas

Comando: script Python usando `load_golden_set`, `run_golden_set`,
`SuitabilityGuardedPolicy` envolvendo `BestHistoricalArmPolicy`,
`ThompsonSamplingPolicy` (prior_strength=4.0, seed=2) e `LinUCBPolicy`
(alpha=1.0), contra `data/golden_set/evaluation_cases.jsonl`.

```
baseline
  safety pass rate: 1.0
  expected-action match rate: 0.18181818181818182
thompson_sampling
  safety pass rate: 1.0
  expected-action match rate: 0.13636363636363635
linucb
  safety pass rate: 1.0
  expected-action match rate: 0.0
```

Taxa de segurança 100% (1.0) para as três políticas guardadas — nenhuma falha
de segurança observada. A taxa de acerto da ação esperada varia entre
políticas (18,2% baseline, 13,6% Thompson Sampling, 0% LinUCB); isso é
esperado e será discutido no relatório final.

## Passo 2: análise de sensibilidade de hiperparâmetros

Comando: `run_replay_simulation` sobre a tabela de treino real
(`build_training_table`), variando `prior_strength` do Thompson Sampling
(seed=2) e `alpha` do LinUCB (seed=3).

```
thompson prior_strength=1.0: mean_regret=0.026678 n=3653
thompson prior_strength=4.0: mean_regret=0.024970 n=3520
thompson prior_strength=10.0: mean_regret=0.031178 n=3349
linucb alpha=0.1: mean_regret=0.038498 n=3087
linucb alpha=1.0: mean_regret=0.029457 n=3343
linucb alpha=5.0: mean_regret=0.037352 n=3219
```

## Passo 3: fairness de exposição entre segmentos de `job`

Comando: crosstab normalizado por linha (`job` x `arm_id`) sobre
`data/synthetic_enrichment/offer_events.csv` unido a
`data/processed/bank_marketing.csv` pela coluna `job`.

```
arm_id         cdb_12m  cdb_24m  fundo_liquidez_diaria  poupanca_programada  reserva_emergencia  taxa_promocional
job
admin.           0.171    0.158                  0.173                0.169               0.165             0.163
blue-collar      0.162    0.171                  0.173                0.160               0.167             0.167
entrepreneur     0.169    0.145                  0.187                0.175               0.157             0.167
housemaid        0.168    0.179                  0.143                0.159               0.179             0.171
management       0.174    0.169                  0.157                0.173               0.162             0.166
retired          0.176    0.166                  0.160                0.160               0.158             0.180
self-employed    0.151    0.174                  0.158                0.170               0.176             0.172
services         0.162    0.167                  0.168                0.175               0.165             0.164
student          0.174    0.173                  0.169                0.145               0.160             0.179
technician       0.163    0.165                  0.166                0.170               0.166             0.170
unemployed       0.149    0.159                  0.179                0.164               0.178             0.173
unknown          0.136    0.185                  0.182                0.148               0.164             0.185

min exposure per (job, arm) cell: 0.13636363636363635
max exposure per (job, arm) cell: 0.18681318681318682
expected under uniform logging (1/6): 0.16666666666666666
```

Todas as células ficam próximas de 1/6 ≈ 0,167, consistente com o logging
uniforme aleatório da Etapa 2.
