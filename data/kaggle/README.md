# Base Kaggle: bank-marketing

- **Fonte:** https://www.kaggle.com/datasets/henriqueyamahata/bank-marketing
- **Licença:** CC0 (domínio público), conforme a página do dataset no Kaggle.
- **Referência original:** Moro, S., Cortez, P., & Rita, P. (2014). Bank Marketing
  [Dataset]. UCI Machine Learning Repository.

## Como baixar

Requer uma conta Kaggle e um token de API. Em
https://www.kaggle.com/settings/api, na seção "API Tokens", dê um nome ao token e
clique em "Generate" — copie o valor mostrado e coloque em `KAGGLE_API_TOKEN` no
seu `.env` local (ver `.env.example`). O token é lido automaticamente do `.env`
pelo próprio loader (via `python-dotenv`), sem precisar exportá-lo manualmente no
shell.

```bash
.venv/bin/python -c "from bandit_platform.data.kaggle_loader import download_dataset; print(download_dataset('data/kaggle/raw'))"
```

Alternativa manual: baixe o arquivo `bank-additional-full.csv` diretamente pela
página do Kaggle acima e salve em `data/kaggle/raw/bank-additional-full.csv`.

O arquivo bruto não é versionado neste repositório (ver `.gitignore`); apenas o
manifesto de proveniência (`sha256`, data do download, referência do dataset) seria
gerado localmente por `write_manifest` — também não versionado, pois é específico de
quem rodou o download.

## Dicionário de dados

O arquivo real hospedado neste dataset Kaggle é `bank-additional-full.csv` — a
variante do UCI Bank Marketing enriquecida com indicadores macroeconômicos (não é
a variante clássica `bank-full.csv`; não existe coluna `balance` aqui).

| Coluna | Tipo | Descrição |
|---|---|---|
| age | inteiro | Idade do cliente |
| job | categórica | Tipo de ocupação |
| marital | categórica | Estado civil |
| education | categórica | Nível de escolaridade |
| default | categórica (yes/no/unknown) | Possui crédito em default? |
| housing | categórica (yes/no/unknown) | Possui financiamento habitacional? |
| loan | categórica (yes/no/unknown) | Possui empréstimo pessoal? |
| contact | categórica | Tipo de contato de comunicação |
| month | categórica | Mês do último contato |
| day_of_week | categórica | Dia da semana do último contato |
| duration | inteiro | Duração em segundos do último contato |
| campaign | inteiro | Número de contatos nesta campanha para este cliente |
| pdays | inteiro | Dias desde o último contato de campanha anterior (999 = nunca contatado) |
| previous | inteiro | Número de contatos antes desta campanha |
| poutcome | categórica | Resultado da campanha anterior (failure/nonexistent/success) |
| emp.var.rate | numérico | Taxa de variação do emprego (indicador trimestral) |
| cons.price.idx | numérico | Índice de preços ao consumidor (indicador mensal) |
| cons.conf.idx | numérico | Índice de confiança do consumidor (indicador mensal) |
| euribor3m | numérico | Taxa Euribor de 3 meses (indicador diário) |
| nr.employed | numérico | Número de empregados (indicador trimestral) |
| y | categórica (yes/no) | Target: o cliente assinou o depósito a prazo? |
| target | binário (0/1) | Derivado de `y` na camada processada (1 = yes, 0 = no) — só existe em `data/processed/`, não no CSV bruto do Kaggle |

Os cinco indicadores macroeconômicos (`emp.var.rate` a `nr.employed`) são
publicados pelo Banco de Portugal e associados ao mês/trimestre do contato — não
são vazamento, pois são conhecidos publicamente no momento da decisão, não
dependem do resultado do contato em si.

## Decisão de vazamento

A coluna `duration` é descartada na camada processada (ver
`src/bandit_platform/data/clean.py`): ela só é conhecida depois que a
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

Foram identificadas 1.784 linhas (~4,3%) totalmente duplicadas na base bruta. Sem
uma coluna de identificação de cliente, não é possível distinguir duplicatas
verdadeiras de coincidências de perfil — a decisão foi documentar e não remover
nesta etapa (ver `reports/data-quality.md`); qualquer remoção futura deve ser
justificada na etapa de modelagem correspondente.
