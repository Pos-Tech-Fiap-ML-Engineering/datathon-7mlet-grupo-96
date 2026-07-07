# Contrato do serviço de decisão

## `POST /decide`

Recebe o contexto de um cliente elegível e devolve a oferta/mensagem escolhida
pela política ativa, com justificativa e versão da política.

### Requisição

```json
{
  "job": "admin.",
  "age": 35,
  "poutcome": "nonexistent",
  "default": "no",
  "previous": 2
}
```

| Campo | Tipo | Obrigatório | Restrição |
|---|---|---|---|
| job | string | sim | categoria de ocupacao (ex.: `admin.`, `technician`, `unknown`) |
| age | inteiro | sim | 18 a 110 |
| poutcome | string | sim | `failure`, `nonexistent` ou `success` |
| default | string | sim | `yes`, `no` ou `unknown` |
| previous | inteiro | sim | >= 0 |

### Resposta (200)

```json
{
  "decision_id": "3f2c1a8e-...-...",
  "arm_id": "cdb_12m",
  "reason_code": "thompson_sampling_v0",
  "policy_version": "thompson_sampling_v1_replay_seed2",
  "timestamp": "2026-07-07T12:00:00+00:00"
}
```

`reason_code` documenta a origem da decisão: `thompson_sampling_v0` (escolha
normal da política adaptativa) ou `suitability_override` (a guarda de
elegibilidade substituiu a escolha original — ver `docs/system-card.md` quando
existir, Etapa 8).

### Exemplo de chamada

```bash
curl -X POST http://localhost:8000/decide \
  -H "Content-Type: application/json" \
  -d '{"job":"admin.","age":35,"poutcome":"nonexistent","default":"no","previous":2}'
```

### Tratamento de erro

- **422 Unprocessable Entity**: campo obrigatório ausente ou fora da restrição
  (ex.: `age` fora de 18-110). O corpo da resposta segue o formato padrão de
  validação do FastAPI/Pydantic, listando o campo e o motivo.
- **500 Internal Server Error**: falha inesperada ao carregar os dados/treinar
  a política (ex.: arquivos de dados ausentes) — verifique se
  `data/processed/bank_marketing.csv` e `data/synthetic_enrichment/*.csv`
  existem (Etapas 1-2).

### Log auditável

Cada chamada bem-sucedida grava uma linha em `logs/decisions.jsonl` (não
versionado) com `decision_id`, `timestamp`, `context`, `arm_id`,
`reason_code`, `policy_version` — permitindo auditoria posterior de qualquer
decisão pelo `decision_id`.

## `GET /health`

Retorna `{"status": "ok"}` — não treina nem consulta a política, só confirma
que o serviço está no ar.

## Nota de performance

A primeira chamada a `/decide` (ou o primeiro `bandit-cli decide`) treina a
política a partir dos dados reais (carrega os CSVs, treina o modelo de
propensão em PyTorch, roda o replay da Etapa 3) — isso pode levar alguns
segundos. Chamadas seguintes usam a política já treinada, cacheada em memória.
