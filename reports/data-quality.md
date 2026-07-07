# Qualidade dos dados — bank-marketing (henriqueyamahata)

Este relatório resume o que a análise exploratória em `notebooks/01_eda.ipynb`
mostrou sobre `data/processed/bank_marketing.csv`, gerada a partir do download real
do dataset Kaggle `henriqueyamahata/bank-marketing` (ver `data/kaggle/README.md`).

## Origem real dos dados

O arquivo efetivamente hospedado nesse dataset Kaggle é `bank-additional-full.csv`
— a variante estendida do UCI Bank Marketing, que inclui indicadores
macroeconômicos (`emp.var.rate`, `cons.price.idx`, `cons.conf.idx`, `euribor3m`,
`nr.employed`) e a coluna `day_of_week` no lugar de `day`. Essa variante **não
contém a coluna `balance`**, presente apenas na variante clássica `bank-full.csv`
(que não está neste dataset Kaggle específico). O dicionário de dados em
`data/kaggle/README.md` já reflete esse schema real: 21 colunas, sem `balance`,
com `day_of_week` no lugar de `day` e os cinco indicadores macroeconômicos.

## Tamanho final e balanço de classes

A camada processada tem **41.188 linhas e 21 colunas** (20 features mais o
`target` binário derivado de `y`, já sem `duration` por vazamento — ver seção
abaixo). O `target` está claramente desbalanceado: **88,7% das linhas são "no"
(36.548) e 11,3% são "yes" (4.640)**, uma razão de aproximadamente 7,9 para 1. Esse
desbalanceamento é relevante para o desenho da plataforma de bandit, já que a
"recompensa" (conversão) é um evento raro.

## Valores ausentes

Não há nenhum valor nulo técnico — `df.isna().sum()` retorna zero em todas as 21
colunas. Isso não significa, porém, que os dados estejam completos: seis colunas
categóricas usam a string `"unknown"` como sentinela de dado ausente. A taxa de
"unknown" varia bastante entre elas: `default` tem **20,9%** de "unknown" (bem
acima das demais), seguida por `education` (4,2%), `housing` e `loan` (2,4% cada),
`job` (0,8%) e `marital` (0,2%). Ou seja, quase 1 em cada 5 registros não tem
informação confiável sobre default de crédito — um ponto de atenção para qualquer
feature derivada dessa coluna.

## Distribuições numéricas e outliers

`pdays` concentra **96,3% das linhas no valor-sentinela 999** ("nunca contatado em
campanha anterior"); portanto não deve ser usada como uma escala numérica contínua
sem antes isolar esse sentinela (por exemplo, com uma flag binária "já foi
contatado antes"). `campaign` é fortemente assimétrica à direita: a mediana é de
apenas 2 contatos por cliente nesta campanha, mas o máximo chega a 56 contatos, com
157 linhas acima de 20 — outliers de esforço de contato que merecem tratamento
(cap/winsorização) antes de qualquer modelagem. `age` varia de 17 a 98 anos (mediana
38), com 119 linhas acima de 80 anos e 75 abaixo de 20 — valores plausíveis, mas
que formam caudas finas na distribuição.

Também identificamos **1.784 linhas totalmente duplicadas** (~4,3% da base) — casos
em que clientes com o mesmo perfil demográfico foram contatados sob o mesmo
contexto macroeconômico (mesmo mês/indicadores), resultando em linhas idênticas em
todas as colunas. Vale investigar/deduplicar antes de treinar qualquer modelo, para
não inflar artificialmente o peso desses perfis.

## Vazamento de dados

A coluna `duration` foi removida na camada processada porque só é conhecida depois
que a ligação termina — no momento de decidir qual oferta apresentar, essa
informação ainda não existe. Mantê-la treinaria um modelo que "sabe o futuro",
vazamento temporal documentado em `data/kaggle/README.md` (seção "Decisão de
vazamento").
