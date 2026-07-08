# Model Card — Políticas de Decisão Adaptativa

## Nome e versão

Este card cobre a família de políticas de bandit contextual desta
plataforma: baseline determinístico, Thompson Sampling (com warm-start via
PyTorch) e LinUCB — não um modelo único e fixo. A versão efetivamente
servida em produção é controlada pelo Policy Registry (Etapa 7,
`src/bandit_platform/mlops/registry.py`) e pode mudar a cada
`bandit-cli promote`. Na ausência de qualquer promoção, o fallback padrão é
`thompson_sampling_v1_replay_seed2` (Thompson Sampling, seed=2,
prior_strength=4.0, treinado via replay sobre a tabela de treino sintética —
`src/bandit_platform/service/active_policy.py`).

## Visão geral

Políticas de multi-armed bandit contextual que decidem, para cada cliente
elegível, qual oferta/mensagem financeira apresentar dentre um catálogo
sintético fixo. O contexto de decisão (`job`, `age`, `poutcome`, `default`,
`previous`) alimenta a política; a escolha é sempre filtrada por um guard de
elegibilidade de negócio (`SuitabilityGuardedPolicy`) antes de ser
retornada.

## Dados de treino

- **Fonte**: Kaggle "bank-marketing" (henriqueyamahata), licença CC0,
  originalmente do UCI Bank Marketing Dataset (Moro, Cortez & Rita, 2014) —
  campanhas de telemarketing bancário português, 2008-2013.
- **Volume**: 41.188 linhas, 21 colunas processadas: `age, job, marital,
  education, default, housing, loan, contact, month, day_of_week, campaign,
  pdays, previous, poutcome, emp.var.rate, cons.price.idx, cons.conf.idx,
  euribor3m, nr.employed, y, target`.
- **Coluna removida por vazamento temporal**: `duration` (só é conhecida
  após a ligação terminar — nunca existiria no momento real da decisão).
  Ver `data/kaggle/README.md` e `reports/data-quality.md`.
- **Valores sentinela `"unknown"`**: presentes em 6 colunas categóricas,
  com destaque para `default` (20,9% das linhas) — ver "Vieses conhecidos"
  abaixo.
- **Desbalanceamento do alvo**: 88,7% "no" / 11,3% "yes" (~7,9:1).
- **Camada sintética de enriquecimento** (Etapa 2, não faz parte do dataset
  Kaggle original): catálogo de ofertas, eventos de impressão/contexto,
  recompensas atrasadas — usada para construir a tabela de treino via
  replay, nunca misturada fisicamente com a base Kaggle
  (`data/synthetic_enrichment/`).

## Dados de avaliação

- **Golden set**: 22 casos curados versionados em
  `data/golden_set/evaluation_cases.jsonl`, cobrindo 4 categorias
  (8 típicos, 5 de borda, 6 adversariais, 3 de cobertura de segmento) e os
  12 segmentos de `job`.
- **Avaliação offline (replay-with-rejection)**: metodologia de Li et al.
  (2011), válida aqui porque a política de logging sintética é uniforme
  aleatória — `reports/offline-evaluation.md`.

## Métricas (fonte: `reports/algorithm-comparison.md` e `reports/offline-evaluation.md`)

| Política | Regret médio/decisão | Decisões aceitas (replay) | Golden-set safety | Golden-set acurácia vs. oráculo |
|---|---|---|---|---|
| baseline | 0.026769 | 3.318 | 100% (22/22) | 18,2% (4/22) |
| **thompson_sampling** | **0.024970** (melhor) | 3.520 | 100% (22/22) | 13,6% (3/22) |
| linucb | 0.029457 | 3.343 | 100% (22/22) | 18,2% (4/22) |

Exposição por segmento (fairness de exposição, não de resultado): mínimo
13,6%, máximo 18,7%, valor teórico uniforme 16,7%, sobre 72 células
(12 segmentos `job` × 6 braços) — todas dentro de ~3 pontos percentuais do
valor uniforme esperado sob a política de logging aleatória.

## Uso pretendido

- Demonstrar, em ambiente de simulação com recompensas sintéticas, como uma
  abordagem de bandit contextual resolveria o problema de seleção adaptativa
  de oferta/mensagem/canal proposto pelo desafio Datathon 7MLET.
- Uso educacional/avaliativo — não uso em decisão financeira real.

## Fora de escopo

- Qualquer uso com dados reais de clientes (PII, CPF, renda, patrimônio).
- Qualquer decisão de crédito ou concessão real.
- Uso da política interna (Thompson Sampling/LinUCB/baseline) sem o wrapper
  `SuitabilityGuardedPolicy` — o guard nunca deve ser removido do caminho de
  serviço.
- Promoção de uma nova versão para produção sem passar pelo gate de
  aprovação humana estruturada do Policy Registry (Etapa 7).
- Deploy fora da arquitetura documentada em `docs/architecture-azure.md`
  (que já prevê Key Vault + Managed Identity para segredos).

## Análise de fairness

A análise realizada (`reports/offline-evaluation.md` §6) mede **fairness de
exposição**: a frequência com que cada segmento de `job` recebe cada braço,
comparada ao valor uniforme teórico. Os resultados (13,6%-18,7% vs. 16,7%
esperado) indicam exposição balanceada sob a política de logging atual.
**Isto não é uma análise de fairness de resultado** (se os braços
recomendados são igualmente benéficos entre segmentos) — essa análise não
foi feita e fica registrada como trabalho futuro.

## Vieses conhecidos

- Segmentos com alta taxa de `"unknown"` em `default` (20,9% das linhas)
  podem ter priors de warm-start (Thompson Sampling) menos confiáveis, já
  que o modelo de propensão via PyTorch aprende a partir desses mesmos
  dados incompletos.
- O desbalanceamento do alvo (7,9:1) significa que o sinal positivo
  disponível para aprendizado é escasso.
- O dataset reflete um contexto histórico e geográfico específico
  (telemarketing bancário português, 2008-2013) — não generaliza
  automaticamente para outros mercados ou períodos.
- O catálogo de ofertas e as regras de negócio são inteiramente fictícios/
  sintéticos (Etapa 2) e não refletem produtos ou políticas comerciais de
  nenhuma instituição real.

## Limitações técnicas

- O guard de suitability implementado em código
  (`src/bandit_platform/policies/suitability.py`) cobre apenas duas das
  regras de negócio documentadas em `data/synthetic_enrichment/policy_docs/`
  (que reúnem bem mais de duas regras ao todo, entre os 5 documentos):
  bloqueio de crédito/investimento quando `default=yes`, e bloqueio de
  `cdb_24m` quando `previous<=0`. Entre as regras documentadas mas **não
  implementadas**, destacam-se "não repetir oferta recusada na mesma
  campanha" e "validade de 30 dias da taxa promocional"
  (`reports/offline-evaluation.md` §7) — ver
  `docs/system-card.md` para o cenário de risco correspondente.
- O golden set é curado (22 casos), não é uma amostra estatisticamente
  representativa da população real de decisões.
- A análise de sensibilidade de hiperparâmetros testou apenas 3×2 = 6
  combinações (`reports/offline-evaluation.md` §5), não é exaustiva.
- A referência "Nilos-UCB" do edital não foi localizada na literatura
  acadêmica; o time substituiu por LinUCB (Li et al., 2010) como resposta à
  família UCB, com a justificativa registrada em
  `reports/algorithm-comparison.md`.
- A política nunca deve rodar em produção sem o guard de suitability
  habilitado.

## Plano de revisão periódica

Este model card deve ser revisado: (1) sempre que `bandit-cli promote`
ativar uma nova versão (a seção "Métricas" deve refletir as métricas do
`PromotionReport` da versão recém-promovida, disponíveis via
`bandit-cli policy-status`); (2) no mínimo a cada ciclo de retreino
documentado em `docs/mlops-lifecycle.md`, mesmo sem promoção. Responsável:
o time que executa a promoção (Grupo 96) — a revisão é parte do próprio
procedimento de `approve`/`promote` descrito na Etapa 7, não uma tarefa
separada e opcional.
