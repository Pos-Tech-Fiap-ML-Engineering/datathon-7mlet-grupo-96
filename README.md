# Datathon 7MLET — Grupo 96 — Plataforma de Experimentação Adaptativa

Plataforma de experimentação adaptativa (multi-armed bandit) para decidir, em
diferentes canais digitais, qual oferta, mensagem ou próximo passo apresentar a
cada cliente elegível de uma instituição financeira fictícia. Projeto construído
para o Datathon da Pós Tech FIAP (7MLET), cobrindo dados, algoritmos de bandit,
avaliação offline, serviço auditável, arquitetura-alvo Azure, ciclo de vida MLOps
e governança.

O desafio completo está descrito em [`Datathon-7MLET.pdf`](./Datathon-7MLET.pdf).

## Escopo

O objetivo não é reproduzir um sistema bancário real, e sim demonstrar
maturidade técnica de ML Engineering: formular o problema, versionar dados,
comparar políticas de decisão (baseline determinístico vs. multi-armed bandit),
avaliar qualidade e risco antes de servir a decisão, expor um serviço auditável,
e documentar como a solução seria operada em produção (Azure + MLOps +
governança). Não são usados dados reais de clientes.

## Escolhas de design

- Base Kaggle: `bank-marketing` (henriqueyamahata).
- Algoritmos: baseline determinístico, Thompson Sampling contextual (com warm
  start via um modelo de propensão em PyTorch) e LinUCB (família UCB).
- Assistente com LLM: LangChain + Anthropic Claude + RAG local sobre documentos
  sintéticos de política comercial/suitability.
- Serviço: FastAPI (contrato oficial) + CLI + Streamlit (demo visual).
- Nuvem-alvo: exclusivamente Azure, com Terraform para IaC.

O raciocínio completo por trás de cada escolha (alternativas consideradas,
trade-offs) está detalhado no relatório técnico da Etapa 8
(`reports/technical-report.md`) e na arquitetura-alvo da Etapa 6
(`docs/architecture-azure.md`).

## Como executar localmente

Pré-requisito: Python 3.11 ou superior.

```bash
git clone <url-do-repositorio>
cd datathon-7mlet-grupo-96
poetry install --with dev        # cria o ambiente e instala todas as dependências
poetry run poe test              # roda a suite de testes
```

Para confirmar o ponto de entrada da CLI:

```bash
poetry run bandit-cli --version
```

Para obter uma decisão via CLI, dado um contexto de cliente:

```bash
poetry run bandit-cli decide --context '{"job":"admin.","age":35,"poutcome":"nonexistent","default":"no","previous":2}'
```

Para subir a API (FastAPI, contrato oficial de decisão) em `http://127.0.0.1:8000`:

```bash
poetry run poe serve
```

Para rodar a demo visual (Streamlit):

```bash
poetry run poe demo
```

## Mapa de pastas

Estrutura atual:

```
src/bandit_platform/
  data/          # ingestao e limpeza do dataset Kaggle (Etapas 1-2)
  synthetic/     # enriquecimento sintetico: catalogo de ofertas e eventos (Etapa 2)
  policies/      # baseline, Thompson Sampling contextual (com warm start), LinUCB (Etapa 3)
  evaluation/    # simulacao offline, metricas e golden set (Etapa 4)
  service/       # FastAPI, contrato de decisao, active policy, audit log (Etapa 5)
  assistant/     # assistente LLM/RAG (LangChain + Claude) sobre policy docs e reports (Etapa 5)
  mlops/         # registro de politicas, criterios de promocao, drift, tracking MLflow (Etapa 7)
  cli.py         # ponto de entrada da CLI (bandit-cli)
streamlit_app/   # demo visual em Streamlit (Etapa 5)
data/
  kaggle/                # dataset bruto (bank-marketing, henriqueyamahata)
  processed/             # dados limpos/tratados
  synthetic_enrichment/  # policy_docs (usados pelo RAG) e eventos sinteticos
  golden_set/            # casos de avaliacao (evaluation_cases.jsonl)
notebooks/       # EDA (01_eda.ipynb)
reports/         # relatorios tecnicos escritos (data-generation, data-quality, algorithm-comparison,
                 # offline-evaluation, technical-report — Etapa 8)
docs/            # contrato de servico, arquitetura-alvo Azure (Etapa 6), ciclo de vida MLOps (Etapa 7),
                 # model card, system card, plano LGPD, material de pitch e demo (Etapa 8)
infra/terraform/ # infraestrutura como codigo para a arquitetura-alvo Azure (Etapa 6)
tests/           # suite de testes automatizados (pytest)
pyproject.toml   # dependencias, versao de Python, ponto de entrada da CLI e tasks Poetry
.env.example     # variaveis de ambiente necessarias (sem valores reais)
```

## Comandos disponíveis

| Comando                  | O que faz                                                              |
|--------------------------|------------------------------------------------------------------------|
| `poetry run poe lint`    | Roda `ruff check` sobre `src/` e `tests/`                              |
| `poetry run poe test`    | Roda a suite de testes automatizados (`pytest`)                        |
| `poetry run poe serve`   | Sobe a API FastAPI (`uvicorn`, com reload) em `http://127.0.0.1:8000` |
| `poetry run poe demo`    | Roda a demo visual em Streamlit (`streamlit_app/app.py`)               |

## Ciclo de vida MLOps — retreino, aprovação e promoção de políticas

O ciclo completo é controlado pela CLI `bandit-cli`. Cada comando atualiza
`models/registry/manifest.json` (registro de versões) e/ou o artefato
`.joblib` da política treinada. O fluxo obrigatório é:

```
retrain  →  approve  →  promote  →  (monitor-drift / rollback)
```

### 1. Ver o estado atual

```bash
poetry run bandit-cli policy-status
```

Mostra a versão ativa, o histórico de versões anteriores (disponíveis para
rollback) e o registro completo de todos os candidatos já criados.

### 2. Retreinar um candidato

```bash
# Thompson Sampling
poetry run bandit-cli retrain \
  --algorithm thompson_sampling \
  --prior-strength 4.0 \
  --seed 2 \
  --notes "descrição da hipótese"

# LinUCB
poetry run bandit-cli retrain \
  --algorithm linucb \
  --alpha 1.0 \
  --seed 2 \
  --notes "descrição da hipótese"
```

O que acontece por baixo:
1. Carrega `data/processed/bank_marketing.csv`, `data/synthetic_enrichment/offer_events.csv` e `delayed_rewards.csv`.
2. Monta a tabela de treino (join interno, ~20 mil eventos com recompensa resolvida).
3. Constrói a política candidata com priors do modelo de propensão PyTorch (Thompson) ou matriz identidade (LinUCB).
4. Treina via replay com rejeição (Li et al., 2011) — passa linha a linha, aceita só quando a escolha da política bate com o braço logado.
5. Avalia contra o golden set (`data/golden_set/evaluation_cases.jsonl`, 22 casos).
6. Verifica os critérios de promoção automática:
   - `golden_set_safety_rate >= 1.0` (100% — sem regressão de segurança)
   - `mean_regret <= 0.03` (teto absoluto)
   - `mean_regret <= active_mean_regret * 1.10` (≤ 10% pior que a política ativa)
7. Salva `models/registry/<version_id>.joblib` (política treinada serializada).
8. Adiciona entrada em `models/registry/manifest.json` com status `pending_approval` (passou) ou `rejected` (falhou).
9. Registra run no MLflow (`mlruns/`) com parâmetros, métricas e tag `version_id`.

### 3. Aprovar o candidato (obrigatório)

```bash
# Candidato que passou nos critérios (status: pending_approval)
poetry run bandit-cli approve \
  --version-id <VERSION_ID> \
  --approver "Nome Sobrenome" \
  --reason "justificativa da aprovação"

# Candidato rejeitado pelos critérios — requer --override explícito
poetry run bandit-cli approve \
  --version-id <VERSION_ID> \
  --approver "Nome Sobrenome" \
  --reason "motivo do override e o que falhou" \
  --override
```

`bandit-cli promote` recusa promover qualquer versão sem aprovação (`ValueError`
explícito). Se `--override` for usado, `approved_via_override: true` fica
permanentemente registrado no `manifest.json`.

### 4. Rejeitar manualmente (qualquer momento)

```bash
poetry run bandit-cli reject \
  --version-id <VERSION_ID> \
  --reason "motivo da rejeição"
```

### 5. Promover para produção

```bash
poetry run bandit-cli promote --version-id <VERSION_ID>
```

Atualiza `active_version` no `manifest.json` e empilha a versão anterior em
`history`. O serviço e o Streamlit carregam a política do `.joblib`
correspondente ao `active_version` na inicialização — sem re-treinar nada.

### 6. Reverter (rollback)

```bash
# Volta para a versão imediatamente anterior
poetry run bandit-cli rollback

# Volta para uma versão específica
poetry run bandit-cli rollback --to <VERSION_ID>
```

Pode ser executado quantas vezes quiser. Cada rollback empilha a versão atual
de volta em `history`, então é possível ir e voltar entre versões livremente.

### 7. Monitorar drift

```bash
poetry run bandit-cli monitor-drift \
  --candidate-version <VERSION_ID>
```

Verifica dois sinais:
- **Drift de features**: PSI de `job` e `poutcome` entre as decisões recentes
  (`logs/decisions.jsonl`) e a distribuição de referência do dataset de treino.
  PSI > 0.2 é sinalizado como mudança significativa.
- **Drift de performance**: compara o `mean_regret` do candidato com o da
  política ativa. Regressão > 10% é sinalizada como `regressed: true`.

### 8. Ver experimentos no MLflow

```bash
poetry run mlflow ui --backend-store-uri sqlite:///mlflow.db
# Acesse http://localhost:5000
```

> O backend é SQLite (`mlflow.db`). Não use `mlflow ui` sem `--backend-store-uri`
> — o MLflow 3.x tenta chamar `/traces/metrics` que não é suportado pelo FileStore,
> gerando erros 500 repetitivos no terminal (funcionalmente inofensivo, mas confuso).

Cada run de `retrain` aparece no experimento `bandit-platform` com a tag
`version_id` que cruza com a entrada correspondente no `manifest.json`.

### Estrutura dos artefatos gerados

```
models/registry/
  manifest.json                        # registro de versões: active_version, history, records
  <version_id>.joblib                  # política treinada serializada (uma por retrain)
logs/
  decisions.jsonl                      # log de auditoria (uma linha JSON por decisão)
mlruns/
  <experiment_id>/<run_id>/            # runs do MLflow (params, metrics, tags)
```

## Status do projeto

Concluído:

- Etapa 0 — organização do projeto (scaffolding, testes de exemplo, automação de setup/lint/test, CI).
- Etapa 1 — carregamento e limpeza dos dados Kaggle, com EDA (`notebooks/01_eda.ipynb`).
- Etapa 2 — enriquecimento sintético: catálogo de ofertas, eventos e policy docs (`data/synthetic_enrichment/`).
- Etapa 3 — algoritmos de decisão: baseline determinístico, Thompson Sampling contextual (com warm start via propensão
  em PyTorch) e LinUCB.
- Etapa 4 — avaliação offline com golden set (`data/golden_set/evaluation_cases.jsonl`) e relatórios técnicos de
  comparação de algoritmos.
- Etapa 5 — serviço FastAPI (contrato oficial) + CLI (`bandit-cli`) + demo Streamlit, com assistente LLM/RAG (
  LangChain + Claude) sobre os policy docs e os relatórios técnicos.
- Etapa 6 — arquitetura-alvo Azure e infraestrutura como código (Terraform) (`docs/architecture-azure.md`,
  `infra/terraform/`).
- Etapa 7 — ciclo de vida MLOps (tracking, retraining, monitoramento) (`docs/mlops-lifecycle.md`,
  `src/bandit_platform/mlops/`).
- Etapa 8 — governança, relatório técnico final e pitch (model card, system card, plano LGPD, relatório técnico e
  material de demo day).

## Licença

Distribuído sob a licença MIT — ver [`LICENSE`](./LICENSE).
