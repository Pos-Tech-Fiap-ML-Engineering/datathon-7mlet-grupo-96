# Checklist antes do demo day

Autoavaliação do grupo contra o checklist oficial do edital, com evidência
para cada item.

- [x] README explica desafio, execução local e limitações; pipeline usa
  base Kaggle compatível com fonte, versão, licença e limitações —
  `README.md`, `data/kaggle/README.md`.
- [x] Base processada e enriquecimento sintético documentados e separados
  da base Kaggle original; experimentos rastreados em MLflow —
  `reports/data-generation.md`, `docs/mlops-lifecycle.md`.
- [x] Baseline e abordagem principal comparados com métricas justificadas;
  análise referencia Thompson Sampling e a família UCB (LinUCB, com
  substituição de "Nilos-UCB" justificada) — `reports/algorithm-comparison.md`.
- [x] Avaliação inclui golden set com pelo menos 20 exemplos (22 casos);
  guardrails testados com cenários adversariais —
  `data/golden_set/evaluation_cases.jsonl`, `reports/offline-evaluation.md`.
- [x] Camada de retreino, teste, aprovação e promoção de novas políticas
  documentada — `docs/mlops-lifecycle.md`.
- [x] Serviço, API, notebook executável ou interface demonstrável funciona
  com instruções claras e log auditável de decisão — `docs/service-contract.md`,
  `logs/decisions.jsonl` (gerado em runtime).
- [x] Arquitetura-alvo e plano de deploy usam exclusivamente serviços
  Azure, com plano de segredos via Key Vault e Managed Identity —
  `docs/architecture-azure.md`.
- [x] Model Card, System Card e plano LGPD completos — `docs/model-card.md`,
  `docs/system-card.md`, `docs/lgpd-plan.md`.
- [x] Pitch separa problema, abordagem, demonstração, evidências, riscos e
  impacto — `docs/pitch/pitch-deck.md`, `docs/pitch/roteiro.md`.
- [x] Pitch cobre FinOps (ROI, custo qualitativo por serviço Azure, TCO) —
  `docs/pitch/pitch-deck.md` (slides 10-11), números de `docs/architecture-azure.md`.
- [x] Pitch justifica arquitetura técnica com diagrama, fronteiras e
  alternativas descartadas e apresenta cenários de escala e redução —
  `docs/pitch/pitch-deck.md` (slides 9-11).
- [ ] Pitch inclui demonstração ao vivo ou gravada da plataforma em
  operação, com plano de contingência (desejável; soma pontos extras) —
  script pronto em `docs/demo-script.md`; a execução ao vivo/gravação em
  si acontece no dia da apresentação, fora do escopo deste repositório.
