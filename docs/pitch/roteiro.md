# Roteiro do pitch (10 minutos + 5 minutos de perguntas)

## Cronograma

| Bloco | Tempo | Slides |
|---|---|---|
| Abertura e problema | 1 min | 1-2 |
| Abordagem algorítmica | 2 min | 3 |
| Dados e demonstração | 2,5 min | 4, 6 |
| Evidências quantitativas | 1,5 min | 5 |
| Governança e MLOps | 1,5 min | 7-8 |
| Arquitetura e FinOps | 1 min | 9-11 |
| Limitações e impacto | 30s | 12-13 |

## Pontos-chave por bloco

**Abertura**: apresentar o problema de negócio exatamente como no edital —
regras fixas e A/B longos não escalam; a resposta é bandit contextual.

**Abordagem**: mencionar as três políticas, e ser direto sobre a
substituição "Nilos-UCB" → LinUCB — não esconder, explicar a pesquisa
feita e por que LinUCB é a resposta correta à família UCB.

**Dados e demonstração**: mostrar a separação física entre base Kaggle e
camada sintética; se possível, rodar uma decisão ao vivo (`bandit-cli
decide` ou a aba de decisão do Streamlit) — ver `docs/demo-script.md`.

**Evidências**: citar os três números centrais (regret 0.024970 vencedor,
100% de safety, fairness 13,6%-18,7%) sem arredondar de forma enganosa.

**Governança e MLOps**: este é o bloco onde a maturidade técnica mais
aparece — mostrar que o approval gate é real (uma rejeição de verdade
aconteceu no passeio guiado documentado), não decorativo.

**Arquitetura e FinOps**: apresentar o diagrama, e ser explícito sobre as
alternativas descartadas (ACR, App Service) e por quê.

**Limitações**: terminar com honestidade — a lacuna do guard de
suitability é a limitação mais importante e deve ser mencionada sem
minimizar, pois já está documentada e a banca vai perguntar sobre ela de
qualquer forma se não for antecipada.

## Perguntas antecipadas (para os 5 minutos)

1. **"Por que vocês usaram LinUCB em vez de Nilos-UCB?"** — Pesquisamos e
   não encontramos essa referência na literatura publicada; documentamos a
   busca em `reports/algorithm-comparison.md` e adotamos LinUCB (Li et al.
   2010) como a resposta padrão da família UCB, com justificativa
   registrada.
2. **"Os dados são reais?"** — Não, é a base pública do Kaggle
   (anonimizada, CC0); toda a camada de recompensas/eventos é sintética,
   gerada com sementes controladas, documentada em
   `reports/data-generation.md`.
3. **"Como vocês garantem que a política não vai violar uma regra de
   negócio?"** — O `SuitabilityGuardedPolicy` intercepta toda decisão antes
   de retornar; mas somos transparentes de que ele cobre apenas 2 das
   regras documentadas hoje — a lacuna está no system card e no model card,
   não escondida.
4. **"Quanto custaria rodar isso de verdade?"** — Estimativa qualitativa de
   ~US$5-10/mês na arquitetura-alvo Azure, com um orçamento real de
   US$20/mês configurado via Terraform como guardrail.
5. **"E se a API da Anthropic cair durante a demo?"** — Ver plano de
   contingência em `docs/demo-script.md`; a aba de decisão e o CLI não
   dependem da Anthropic, só o assistente RAG depende.
6. **"O sistema está pronto para produção real?"** — Não, e o próprio
   documento de avaliação do desafio pede que isso fique claro: este é um
   protótipo de demonstração de metodologia, com limitações documentadas
   (`docs/system-card.md`) que precisam ser resolvidas antes de qualquer
   uso regulado real.
7. **"Como funciona o rollback?"** — `bandit-cli rollback` volta para a
   versão anterior usando o histórico do registro; documentado com um
   exemplo real executado em `docs/mlops-lifecycle.md`.
8. **"Por que Thompson Sampling e não LinUCB como padrão?"** — Thompson
   Sampling teve o menor regret médio observado (0.024970 vs. 0.029457) na
   avaliação offline — decisão baseada em dado, não preferência.
