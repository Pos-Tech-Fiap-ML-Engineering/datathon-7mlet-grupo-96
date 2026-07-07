# Avaliação offline: golden set, sensibilidade e fairness

Este relatório interpreta os resultados da avaliação offline conduzida na
Etapa 4 — um golden set de casos curados manualmente contra as três políticas
de bandit já comparadas na Etapa 3 (`reports/algorithm-comparison.md`), uma
análise de sensibilidade de hiperparâmetros e uma análise de fairness de
exposição entre segmentos de `job` — e consolida essas evidências com as
métricas de recompensa/regret/entropia já medidas na Etapa 3. Todos os números
citados abaixo são saída literal de comandos executados contra os dados reais
das Etapas 1-2; nenhum foi estimado.

## 1. Composição do golden set e cálculo do oráculo

O golden set (`data/golden_set/evaluation_cases.jsonl`) tem **22 casos**
versionados, distribuídos em **4 categorias**:

| Categoria | Casos | Propósito |
|---|---|---|
| `typical` | 8 | Perfis de cliente comuns, sem restrição de suitability ativa. |
| `edge` | 5 | Valores extremos (idade 18 e 95 anos, `previous=56`, categorias `unknown`, sentinela `pdays=999`). |
| `adversarial` | 6 | Tentativas deliberadas de obter um braço de crédito/investimento com `default=yes` ou `previous=0`, cenários em que a guarda de suitability precisa vetar o braço. |
| `segment_coverage` | 3 | Segmentos de `job` não representados nos casos típicos (`housemaid`, `unknown`, `entrepreneur` com `default=unknown`). |

Juntas, as 22 linhas cobrem **12 segmentos de `job`** — exatamente as 12
categorias de `job` existentes na base real (`admin.`, `blue-collar`,
`entrepreneur`, `housemaid`, `management`, `retired`, `self-employed`,
`services`, `student`, `technician`, `unemployed`, `unknown`), as mesmas 12
linhas que aparecem na tabela de fairness da Seção 6. Nenhum segmento de
`job` fica sem pelo menos um caso de teste.

`expected_action` e `expected_reward` **não** são um julgamento manual da
equipe: para cada caso, primeiro se calcula o conjunto de braços elegíveis
sob a mesma guarda de suitability usada em produção (`eligible_arms`, contexto
isolado do caso — `default`, `previous`), e só então se escolhe, **dentro
desse subconjunto elegível**, o braço que maximiza `oracle_expected_reward` —
a mesma função-oráculo do simulador de replay da Etapa 3, que conhece os
parâmetros reais de geração da Etapa 2 (`ARM_CONVERSION_EFFECT` e
`CHANNEL_ENGAGEMENT_RATE`). `expected_reward` é o valor esperado desse braço
vencedor sob o oráculo. Restringir a busca aos braços elegíveis é o que
garante, por construção, que `expected_action` nunca esteja em
`forbidden_arms` em nenhum dos 22 casos — o golden set não pede a nenhuma
política que escolha entre segurança e otimalidade; a resposta correta já é
sempre seguramente elegível.

## 2. Resultado de segurança

Rodando o golden set contra as três políticas, cada uma envolvida pela mesma
`SuitabilityGuardedPolicy`:

| Política | Taxa de segurança (`passed_safety`) |
|---|---|
| baseline | 100% (22/22) |
| thompson_sampling | 100% (22/22) |
| linucb | 100% (22/22) |

Nenhuma falha de segurança foi observada, incluindo nos 6 casos
`adversarial` desenhados especificamente para testar a guarda (cliente com
`default=yes` tentando obter crédito/investimento, cliente com `previous=0`
tentando obter `cdb_24m`). O ponto importante aqui é **o que esse 100%
comprova e o que ele não comprova**: como as três políticas são chamadas por
trás da mesma `SuitabilityGuardedPolicy`, é a guarda — não a lógica de decisão
interna de cada política — que veta um braço proibido antes de ele ser
retornado ao chamador. O resultado idêntico (100%) nas três políticas é
exatamente o que se espera se a guarda estiver correta e for a única
responsável por aplicar as regras de suitability: ele valida a **guarda**,
não indica que `BestHistoricalArmPolicy`, `ThompsonSamplingPolicy` ou
`LinUCBPolicy` "sabem", cada uma por si, respeitar `default=yes` ou
`previous=0` — nenhuma das três tem essa regra embutida em sua própria lógica
de seleção. Se a guarda fosse removida ou tivesse um defeito, é bem possível
que alguma das políticas de fato escolhesse um braço proibido nos casos
adversariais (é exatamente para testar isso que esses 6 casos existem).

## 3. Resultado de otimalidade

**Nota metodológica (já registrada na coleta de dados):** a primeira versão
desta avaliação testou Thompson Sampling e LinUCB como instâncias frescas,
sem nenhum treino prévio — o que é injusto e, no caso do LinUCB, produz um
artefato de desempate por ordem de catálogo (golden set é avaliado em modo
one-shot, sem `policy.update()` entre casos; um LinUCB com `A=identity`
inicial gera o mesmo escore de bônus para todos os braços em todo caso, então
`max()` sempre escolhe o primeiro braço do catálogo — taxa de acerto 0/22 sem
nenhum sinal real sobre a política). A versão corrigida — e a única
reportada aqui — primeiro treina Thompson Sampling e LinUCB via a mesma
simulação de replay usada no relatório de comparação de algoritmos
(`run_replay_simulation` sobre a tabela de treino completa; seed=2 para
Thompson Sampling com priors de warm-start `prior_strength=4.0`, seed=3 para
LinUCB com `alpha=1.0`), e só então congela cada política treinada para
avaliá-la contra o golden set. O baseline (`BestHistoricalArmPolicy`) segue
treinado via `.fit()` sobre os dados reais, como sempre. Ou seja: as três
políticas chegam ao golden set já tendo "visto" a base histórica completa —
nenhuma é avaliada a frio.

| Política | Taxa de acerto da ação esperada |
|---|---|
| baseline | 18,2% (4/22) |
| thompson_sampling | 13,6% (3/22) |
| linucb | 18,2% (4/22) |

Mesmo treinadas via replay completo, **nenhuma das três políticas chega perto
de 100%** — e isso é o resultado esperado, não um defeito de nenhuma delas.
`expected_action` é o braço elegível que maximiza a recompensa esperada sob a
função de recompensa **verdadeira** do simulador para o contexto exato
daquele caso — um padrão-ouro que nenhuma política aprende a reproduzir
perfeitamente, porque nenhuma das três foi desenhada para replicar um oráculo
caso a caso; foram desenhadas para aprender boas decisões a partir da
experiência (histórico ou replay), o que é uma tarefa diferente e mais dura.
Em particular:

- **Thompson Sampling** escolhe braços **amostrando** de sua posterior
  (`Beta` por segmento×braço) a cada chamada — por desenho, isso significa
  que ela vai escolher deliberadamente um braço que não é o de maior média
  posterior em uma fração dos casos (é exatamente esse o mecanismo de
  exploração). Por isso não é surpreendente que, neste golden set de 22
  casos, ela tenha a menor taxa de acerto (13,6%) das três: uma parcela dos
  "erros" aqui é exploração intencional, não um sinal de que a política é
  pior — no comparativo mais amplo da Etapa 3 (3.520 decisões aceitas via
  replay), Thompson Sampling teve o **menor regret médio** das três
  políticas (ver Seção 4), o que é a leitura mais confiável de qualidade de
  decisão disponível.
- **LinUCB e o baseline** empatam em 18,2% (4/22 cada). Isso não deve ser lido
  como "LinUCB é equivalente ao baseline" de forma geral — 22 casos é uma
  amostra pequena o suficiente para que esse tipo de empate aconteça por
  coincidência (o mesmo tipo de coincidência de amostra pequena já observado
  em outras métricas desta avaliação, ver Seção 4). O que o número mostra de
  concreto é que, depois de corrigido o artefato de cold-start, o
  comportamento "como servido" do LinUCB deixou de ser degenerado e passou a
  produzir escolhas tão alinhadas ao oráculo quanto a regra fixa do baseline
  neste conjunto específico de casos.
- Nenhuma das três abordagens (regra fixa de melhor braço histórico,
  amostragem bayesiana por segmento, banda linear contextual com bônus de
  incerteza) tem qualquer garantia teórica de bater um oráculo caso a caso —
  bater esse oráculo com frequência alta exigiria, na prática, conhecer a
  função de recompensa verdadeira, o que nenhuma política tem acesso durante
  o treino (só o processo de avaliação tem, para poder pontuar as
  políticas). A mesma ressalva de hindsight já documentada em
  `reports/algorithm-comparison.md` para a comparação da Etapa 3 se aplica
  aqui: comparar taxas de acerto de forma ingênua, sem entender o mecanismo
  por trás de cada política, leva a conclusões erradas.

## 4. Matriz consolidada de métricas (Etapas 3 e 4)

| Política | Decisões aceitas (replay, Etapa 3) | Recompensa acumulada | Recompensa média | Regret acumulado | Regret médio | Entropia de seleção | Taxa de segurança (golden set) | Taxa de acerto (golden set) |
|---|---|---|---|---|---|---|---|---|
| baseline | 3.318 | 601,0 | 0,1811 | 88,8193 | 0,026769 | 1,0691 | 100% | 18,2% (4/22) |
| thompson_sampling | 3.520 | 543,0 | 0,1543 | 87,8930 | 0,024970 | 1,5349 | 100% | 13,6% (3/22) |
| linucb | 3.343 | 464,0 | 0,1388 | 98,4746 | 0,029457 | 1,6940 | 100% | 18,2% (4/22) |

As seis primeiras colunas (decisões aceitas até entropia de seleção) são as
mesmas medidas em `reports/algorithm-comparison.md`, reunidas aqui com as
duas métricas novas da Etapa 4 (segurança e acerto do golden set) para dar
uma visão única de cada política. Lendo a tabela em conjunto: Thompson
Sampling tem o **menor regret médio** (0,024970) e **entropia maior que o baseline**
(1,5349 vs. 1,0691), ficando porém atrás do LinUCB (1,6940) em exploração. Isso é
consistente com sua taxa de acerto mais baixa no
golden set — ela explora mais e por isso "erra" mais em relação a um oráculo
determinístico, mas decide melhor em valor esperado no agregado. O baseline
tem a maior recompensa acumulada/média, mas isso reflete a vantagem de
hindsight de ser ajustado sobre a tabela de treino inteira antes do replay
começar (ver `reports/algorithm-comparison.md`), não superioridade de
decisão. As três políticas têm taxa de segurança idêntica (100%) porque essa
métrica mede a guarda compartilhada, não a política em si (Seção 2).

## 5. Análise de sensibilidade de hiperparâmetros

Variação de `prior_strength` (Thompson Sampling, seed=2) e `alpha` (LinUCB,
seed=3) sobre a mesma simulação de replay da tabela de treino real:

| Política | Hiperparâmetro | Regret médio | Decisões aceitas |
|---|---|---|---|
| thompson_sampling | `prior_strength=1.0` | 0,026678 | 3.653 |
| thompson_sampling | `prior_strength=4.0` | 0,024970 | 3.520 |
| thompson_sampling | `prior_strength=10.0` | 0,031178 | 3.349 |
| linucb | `alpha=0.1` | 0,038498 | 3.087 |
| linucb | `alpha=1.0` | 0,029457 | 3.343 |
| linucb | `alpha=5.0` | 0,037352 | 3.219 |

(O número de decisões aceitas varia entre configurações pelo mesmo motivo já
registrado em `reports/algorithm-comparison.md`: o replay com rejeição só
aceita uma linha quando a escolha da política coincide com o braço logado, e
essa escolha depende da própria configuração testada — por isso o regret
médio, não o volume de decisões aceitas, é a métrica comparável entre
configurações.)

Os seis números formam um "U" em ambos os hiperparâmetros, não uma relação
puramente monotônica:

- **Thompson Sampling**: `prior_strength=4.0` (o valor usado em todas as
  outras seções deste relatório e em `reports/algorithm-comparison.md`) tem o
  menor regret médio dos três (0,024970). Um prior mais fraco
  (`prior_strength=1.0`, regret 0,026678) dá pouco peso ao warm-start
  informado pelo modelo de propensão, deixando a política mais sujeita ao
  ruído das primeiras atualizações reais do replay; um prior mais forte
  (`prior_strength=10.0`, regret 0,031178, pior que os outros dois) faz o
  oposto — a posterior demora mais para se afastar da crença inicial mesmo
  quando a evidência real do replay já discorda dela. Em outras palavras:
  mais força de prior favorece decisões mais conservadoras logo no início
  (mais peso ao cold-start informado, menos ao que a própria política está
  observando), mas o excesso disso também tem custo de regret, não só o
  déficit.
- **LinUCB**: `alpha=1.0` (também o valor usado nas demais seções) tem o
  menor regret médio (0,029457). `alpha=0.1` (bônus de incerteza pequeno,
  pouca exploração) tem o pior regret dos seis (0,038498) — a política
  compromete-se cedo demais com uma estimativa ainda pouco informada.
  `alpha=5.0` (bônus de incerteza grande, mais exploração) também piora o
  regret (0,037352) em relação a `alpha=1.0`, gastando decisões em braços
  cuja incerteza é alta mas cujo valor real não compensa a aposta. Ou seja,
  mais `alpha` no LinUCB de fato empurra a política para mais exploração,
  mas os dados mostram que isso só reduz regret até um ponto — depois disso,
  exploração adicional volta a aumentar o regret de curto prazo, confirmando
  a intuição de que mais exploração tem um custo de regret que só compensa
  até certo ponto.

## 6. Análise de fairness de exposição entre segmentos de `job`

O crosstab normalizado por linha (`job` × `arm_id`) sobre os eventos
sintéticos da Etapa 2 (`offer_events.csv` unido a `bank_marketing.csv` por
`job`) mostra:

- Exposição mínima observada em qualquer célula (`job`, `arm_id`):
  **13,6%** (0,13636363636363635).
- Exposição máxima observada em qualquer célula: **18,7%**
  (0,18681318681318682).
- Valor esperado sob logging uniforme entre 6 braços (1/6): **16,7%**
  (0,16666666666666666).

Todas as 72 células da tabela (12 segmentos de `job` × 6 braços) ficam dentro
de uma faixa estreita ao redor de 1/6 — a maior distância observada em
relação ao valor teórico é de pouco mais de 3 pontos percentuais, para
qualquer um dos dois extremos. Isso é consistente com a política de logging
usada para gerar `offer_events.csv` na Etapa 2
(`logging_policy = "random_uniform_v0"`, sorteio uniforme entre os 6 braços
independente do cliente) e serve como evidência de que **nenhum segmento de
`job` foi sistematicamente privado de exposição a nenhum braço** durante a
coleta de dados histórica — pré-condição necessária para que qualquer
avaliação offline baseada nesse histórico (replay com rejeição, golden set)
não esteja simplesmente reproduzindo um viés de coleta pré-existente.

## 7. Limitações, vieses e condições em que a política não deve ser usada

- **A guarda de suitability cobre apenas duas das regras de negócio
  documentadas.** `SuitabilityGuardedPolicy` veta braços com base em sinais
  presentes no contexto isolado de uma única decisão — `default=yes` bloqueia
  braços de crédito/investimento, `previous=0` bloqueia `cdb_24m`. As demais
  regras documentadas nas políticas de produto (não reofertar a mesma oferta
  ao mesmo cliente duas vezes, validade de 30 dias do aviso promocional)
  dependem de **histórico de interações ao longo do tempo** — informação que
  o contexto de uma única chamada a `select_arm` não carrega e que não está
  implementada em código nesta etapa, apenas descrita nos documentos de
  política. Isso significa que, tal como está, a política pode reofertar a
  mesma oferta repetidamente ou ignorar a janela de validade de 30 dias de um
  aviso promocional, porque nada no pipeline atual impede isso.
- **O golden set é curado manualmente, não é uma amostra estatística.** Os 22
  casos foram desenhados pela equipe para cobrir cenários julgados relevantes
  (perfis típicos, valores extremos, tentativas adversariais de burlar a
  guarda, segmentos de `job` sub-representados) — não foram amostrados
  aleatoriamente da população real de clientes. Um resultado de 100% de
  segurança e uma taxa de acerto de 13,6%-18,2% neste conjunto são evidência
  de comportamento correto nos cenários antecipados pela equipe, não uma
  garantia estatística de que a mesma taxa se sustente sobre a distribuição
  completa de contextos possíveis.
- **A varredura de sensibilidade testou um subconjunto pequeno do espaço de
  hiperparâmetros**, três valores para `prior_strength` (1,0 / 4,0 / 10,0) e
  três para `alpha` (0,1 / 1,0 / 5,0) — seis combinações no total, não uma
  busca exaustiva. É possível que exista uma configuração com regret médio
  ainda menor fora desses seis pontos (por exemplo, entre `prior_strength=1`
  e `4`, ou entre `alpha=0,1` e `1`); os valores `prior_strength=4,0` e
  `alpha=1,0` usados no restante deste relatório são os melhores **dentro da
  grade testada**, não comprovadamente ótimos em um sentido mais amplo.
- **A política nunca deve ser colocada em produção sem a guarda de
  suitability habilitada.** O resultado de 100% de segurança medido na Seção
  2 é um resultado da guarda, não das políticas de bandit isoladamente —
  nenhuma das três (`BestHistoricalArmPolicy`, `ThompsonSamplingPolicy`,
  `LinUCBPolicy`) tem as regras de `default`/`previous` embutidas em sua
  própria lógica de seleção. Removida a guarda, essas duas regras deixam de
  ser aplicadas e as regras dependentes de histórico continuam sem nenhuma
  aplicação (ver primeiro ponto acima) — ou seja, sem a guarda ativa não há
  nenhuma camada de segurança de suitability em produção.
