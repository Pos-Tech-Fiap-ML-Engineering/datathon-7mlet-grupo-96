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

## Mapa de pastas

Estrutura atual (Etapa 0 — apenas scaffolding):

```
src/bandit_platform/   # pacote Python principal (cli.py hoje; demais modulos nas proximas etapas)
tests/                 # suite de testes automatizados (pytest)
Makefile               # comandos de setup/lint/test
pyproject.toml         # dependencias, versao de Python, ponto de entrada da CLI
.env.example           # variaveis de ambiente necessarias (sem valores reais)
```

Estrutura planejada para as próximas etapas:

```
data/{kaggle,processed,synthetic_enrichment,golden_set}/  # Etapas 1-2
notebooks/                                                # Etapa 1 (EDA)
docs/                                                      # Etapas 6-8 (arquitetura Azure, model card, system card, plano LGPD)
reports/                                                  # Etapas 2 e 8 (data-generation.md, technical-report.md)
streamlit_app/                                            # Etapa 5
infra/terraform/                                          # Etapa 6
```

## Comandos disponíveis

| Comando | O que faz |
|---|---|
| `make setup` | Cria `.venv` e instala o pacote em modo editável com dependências de desenvolvimento |
| `make lint` | Roda `ruff check` sobre `src/` e `tests/` |
| `make test` | Roda a suite de testes automatizados (`pytest`) |

## Limitações desta etapa

Este README reflete o estado da **Etapa 0 (organização do projeto)**: só existe
scaffolding do pacote Python, testes de exemplo, automação de setup/lint/test e
CI. Carregamento de dados, enriquecimento sintético, algoritmos de bandit,
avaliação, serviço, arquitetura Azure, MLOps e governança serão adicionados nas
Etapas 1 a 8.

## Licença

Distribuído sob a licença MIT — ver [`LICENSE`](./LICENSE).
