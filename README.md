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
trade-offs) será detalhado no relatório técnico da Etapa 8
(`reports/technical-report.md`) e na arquitetura-alvo da Etapa 6
(`docs/architecture-azure.md`), à medida que essas etapas forem entregues.

## Como executar localmente

Pré-requisito: Python 3.11 ou superior.

```bash
git clone <url-do-repositorio>
cd datathon-7mlet-grupo-96
make setup   # cria .venv e instala o pacote em modo editavel + deps de dev
make test    # roda a suite de testes automatizados
```

Para confirmar o ponto de entrada da CLI:

```bash
.venv/bin/bandit-cli --version
```

Para obter uma decisão via CLI, dado um contexto de cliente:

```bash
.venv/bin/bandit-cli decide --context '{"job":"admin.","age":35,"poutcome":"nonexistent","default":"no","previous":2}'
```

Para subir a API (FastAPI, contrato oficial de decisão) em `http://127.0.0.1:8000`:

```bash
make serve
```

Para rodar a demo visual (Streamlit):

```bash
make demo
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
  cli.py         # ponto de entrada da CLI (bandit-cli)
streamlit_app/   # demo visual em Streamlit (Etapa 5)
data/
  kaggle/                # dataset bruto (bank-marketing, henriqueyamahata)
  processed/             # dados limpos/tratados
  synthetic_enrichment/  # policy_docs (usados pelo RAG) e eventos sinteticos
  golden_set/            # casos de avaliacao (evaluation_cases.jsonl)
notebooks/       # EDA (01_eda.ipynb)
reports/         # relatorios tecnicos escritos (data-generation, data-quality, algorithm-comparison, offline-evaluation)
docs/            # contrato de servico (service-contract.md)
tests/           # suite de testes automatizados (pytest)
Makefile         # comandos de setup/lint/test/serve/demo
pyproject.toml   # dependencias, versao de Python, ponto de entrada da CLI
.env.example     # variaveis de ambiente necessarias (sem valores reais)
```

Ainda planejado (Etapas 6-8): `infra/terraform/` (arquitetura-alvo Azure) e
documentos adicionais em `docs/` e `reports/` — arquitetura Azure, model card,
system card, plano LGPD e o relatório técnico final
(`reports/technical-report.md`).

## Comandos disponíveis

| Comando | O que faz |
|---|---|
| `make setup` | Cria `.venv` e instala o pacote em modo editável com dependências de desenvolvimento |
| `make lint` | Roda `ruff check` sobre `src/` e `tests/` |
| `make test` | Roda a suite de testes automatizados (`pytest`) |
| `make serve` | Sobe a API FastAPI (`uvicorn`, com reload) em `http://127.0.0.1:8000` |
| `make demo` | Roda a demo visual em Streamlit (`streamlit_app/app.py`) |

## Status do projeto

Concluído:

- Etapa 0 — organização do projeto (scaffolding, testes de exemplo, automação de setup/lint/test, CI).
- Etapa 1 — carregamento e limpeza dos dados Kaggle, com EDA (`notebooks/01_eda.ipynb`).
- Etapa 2 — enriquecimento sintético: catálogo de ofertas, eventos e policy docs (`data/synthetic_enrichment/`).
- Etapa 3 — algoritmos de decisão: baseline determinístico, Thompson Sampling contextual (com warm start via propensão em PyTorch) e LinUCB.
- Etapa 4 — avaliação offline com golden set (`data/golden_set/evaluation_cases.jsonl`) e relatórios técnicos de comparação de algoritmos.
- Etapa 5 — serviço FastAPI (contrato oficial) + CLI (`bandit-cli`) + demo Streamlit, com assistente LLM/RAG (LangChain + Claude) sobre os policy docs e os relatórios técnicos.

Pendente:

- Etapa 6 — arquitetura-alvo Azure e infraestrutura como código (Terraform).
- Etapa 7 — ciclo de vida MLOps (tracking, retraining, monitoramento).
- Etapa 8 — governança, relatório técnico final e pitch.

## Licença

Distribuído sob a licença MIT — ver [`LICENSE`](./LICENSE).
