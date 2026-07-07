# Base Kaggle: bank-marketing

- **Fonte:** https://www.kaggle.com/datasets/henriqueyamahata/bank-marketing
- **Licença:** CC0 (domínio público), conforme a página do dataset no Kaggle.
- **Referência original:** Moro, S., Cortez, P., & Rita, P. (2014). Bank Marketing
  [Dataset]. UCI Machine Learning Repository.

## Como baixar

Requer uma conta Kaggle e um token de API (`KAGGLE_USERNAME`/`KAGGLE_KEY` no seu
`.env` local — ver `.env.example`).

```bash
.venv/bin/python -c "from bandit_platform.data.kaggle_loader import download_dataset; print(download_dataset('data/kaggle/raw'))"
```

Alternativa manual: baixe o arquivo `bank-full.csv` (ou `bank.csv`) diretamente pela
página do Kaggle acima e salve em `data/kaggle/raw/bank-full.csv`.

O arquivo bruto não é versionado neste repositório (ver `.gitignore`); apenas o
manifesto de proveniência (`sha256`, data do download, referência do dataset) seria
gerado localmente por `write_manifest` — também não versionado, pois é específico de
quem rodou o download.

## Dicionário de dados

| Coluna | Tipo | Descrição |
|---|---|---|
| age | inteiro | Idade do cliente |
| job | categórica | Tipo de ocupação |
| marital | categórica | Estado civil |
| education | categórica | Nível de escolaridade |
| default | categórica (yes/no) | Possui crédito em default? |
| balance | inteiro | Saldo médio anual (euros) |
| housing | categórica (yes/no) | Possui financiamento habitacional? |
| loan | categórica (yes/no) | Possui empréstimo pessoal? |
| contact | categórica | Tipo de contato de comunicação |
| day | inteiro | Dia do mês do último contato |
| month | categórica | Mês do último contato |
| duration | inteiro | Duração em segundos do último contato |
| campaign | inteiro | Número de contatos nesta campanha para este cliente |
| pdays | inteiro | Dias desde o último contato de campanha anterior (-1 = nunca contatado) |
| previous | inteiro | Número de contatos antes desta campanha |
| poutcome | categórica | Resultado da campanha anterior |
| y | categórica (yes/no) | Target: o cliente assinou o depósito a prazo? |

## Decisão de vazamento

A coluna `duration` é descartada na camada processada (ver
`src/bandit_platform/data/clean.py`, Task 2): ela só é conhecida depois que a
ligação termina, ou seja, no momento de decidir qual oferta/mensagem apresentar ela
ainda não existe. Mantê-la treinaria um modelo que "sabe o futuro" — vazamento
temporal clássico deste dataset, documentado também na literatura original do UCI
Bank Marketing. As demais colunas (`pdays`, `previous`, `poutcome`) descrevem
campanhas *anteriores*, não a atual, e por isso são mantidas como contexto legítimo
disponível no momento da decisão.

## Limitações

Dataset de campanhas de telemarketing bancário português (2008–2013), não
representa necessariamente o comportamento de clientes em canais digitais atuais —
usado aqui como proxy de propensão à conversão, conforme o próprio edital do
desafio autoriza.
