# Comparação de políticas de bandit: baseline vs. Thompson Sampling vs. LinUCB

Este relatório documenta a execução real das três políticas de bandit implementadas
na Etapa 3 — `BestHistoricalArmPolicy` (baseline), `ThompsonSamplingPolicy`
(política adaptativa principal) e `LinUCBPolicy` (família UCB) — contra a base
completa da Etapa 1 (`data/processed/bank_marketing.csv`, 41.188 linhas) enriquecida
com os eventos e recompensas atrasadas sintéticos da Etapa 2
(`data/synthetic_enrichment/offer_events.csv` e `delayed_rewards.csv`), usando o
simulador de replay com rejeição (`run_replay_simulation`). Todos os números
abaixo foram observados diretamente na saída do comando reproduzido a seguir —
nenhum foi estimado ou inventado.

## Comando executado e saída

```
$ poetry run python -c "<script do Step 1 da task brief>"
baseline
  accepted decisions: 3318
  cumulative reward: 601.0
  mean realized reward: 0.1811332127787824
  cumulative regret: 88.81925
  mean regret per decision: 0.026768911995177818
  arm selection entropy: 1.0690969139123754
thompson_sampling
  accepted decisions: 3520
  cumulative reward: 543.0
  mean realized reward: 0.15426136363636364
  cumulative regret: 87.89299999999999
  mean regret per decision: 0.02496960227272727
  arm selection entropy: 1.534887483432454
linucb
  accepted decisions: 3343
  cumulative reward: 464.0
  mean realized reward: 0.13879748728686808
  cumulative regret: 98.474625
  mean regret per decision: 0.029456962309303024
  arm selection entropy: 1.6940274824832982
```

A tabela de treino (`build_training_table`, join de `offer_events.csv` com
`delayed_rewards.csv` e o contexto `job`/`age`/`poutcome`/`target` de
`bank_marketing.csv`) tem **20.032 linhas** — exatamente os eventos que engajaram
(`intermediate_reward == 1`) e por isso têm `final_reward` resolvido em
`delayed_rewards.csv` (ver `reports/data-generation.md`).

## Metodologia de avaliação

A avaliação usa **replay com rejeição** (*rejection sampling*, Li et al., 2011 —
"Unbiased Offline Evaluation of Contextual-bandit-based News Article Recommendation
Algorithms"), implementado em `run_replay_simulation`
(`src/bandit_platform/evaluation/simulate.py`): a tabela histórica é embaralhada com
uma seed própria por política, e para cada linha a política avaliada recebe o mesmo
contexto (`job`, `age`, `poutcome`) que o cliente real viu e escolhe um braço. Se a
escolha da política **não** coincidir com o braço que foi de fato mostrado ao
cliente (`arm_id` logado), a linha é descartada (nem conta como decisão, nem chama
`policy.update`). Se coincidir, a linha é aceita: a política aprende com a
recompensa final real daquele evento (`policy.update`), e o regret é calculado
contra um oráculo que conhece a função de recompensa verdadeira do simulador.

Esse método só produz uma estimativa **não enviesada** do desempenho de uma política
quando a política de *logging* histórica tem probabilidade conhecida e não-nula de
escolher qualquer braço, independente do contexto — e é exatamente esse o caso aqui:
`offer_events.csv` foi gerado com `logging_policy = "random_uniform_v0"`
(`simulate_offer_events`, `src/bandit_platform/synthetic/events.py`), sorteio
uniforme entre os 6 braços via `rng.choice(offer_ids, size=n)` sem pesos e sem
depender do cliente. Isso garante que a taxa de aceitação esperada para qualquer
política determinística ou estocástica gire em torno de 1/6 ≈ 16,67% por
construção — o que de fato se observa nos três resultados (16,56%, 17,57% e
16,69%, ver seção seguinte), uma confirmação indireta de que a premissa de
logging uniforme se sustenta na amostra real.

A limitação conhecida desse método é justamente essa: ele **descarta a maioria dos
eventos logados** — a taxa de aceitação real observada (decisões aceitas / total de
linhas da tabela de treino, 20.032) foi:

| Política | Decisões aceitas | Taxa de aceitação |
|---|---|---|
| baseline | 3.318 | 16,56% |
| thompson_sampling | 3.520 | 17,57% |
| linucb | 3.343 | 16,69% |

Ou seja, entre 82% e 83% dos 20.032 eventos com recompensa resolvida são
simplesmente ignorados em cada avaliação, porque o braço que a política teria
escolhido não é o braço que o histórico registrou. Isso é o preço de uma avaliação
offline não enviesada sem simulador completo do ambiente: ganha-se uma estimativa
correta do valor esperado, mas ao custo de eficiência estatística (amostra efetiva
muito menor que a base bruta).

## Comparação quantitativa

| Política | Decisões aceitas | Recompensa acumulada | Recompensa média | Regret acumulado | Regret médio | Entropia de seleção |
|---|---|---|---|---|---|---|
| baseline | 3.318 | 601,0 | 0,1811 | 88,8193 | 0,026769 | 1,0691 |
| thompson_sampling | 3.520 | 543,0 | 0,1543 | 87,8930 | 0,024970 | 1,5349 |
| linucb | 3.343 | 464,0 | 0,1388 | 98,4746 | 0,029457 | 1,6940 |

(Entropia máxima possível para 6 braços equiprováveis: ln(6) ≈ 1,7918 — nenhuma das
três políticas satura esse teto, mas LinUCB e Thompson Sampling ficam
consideravelmente mais próximos dele do que o baseline determinístico.)

Dois pontos merecem destaque antes de qualquer conclusão, porque a leitura ingênua
da tabela ("baseline tem a maior recompensa, logo é a melhor política") é enganosa:

1. **O número de decisões aceitas difere entre as três políticas** (3.318 vs. 3.520
   vs. 3.343), porque cada rejeição depende da própria escolha da política, então a
   recompensa e o regret *acumulados* não são diretamente comparáveis entre
   políticas — apenas as médias por decisão (`recompensa média`, `regret médio`)
   são comparáveis com um mínimo de rigor.
2. Mesmo nas médias, `thompson_sampling` tem **recompensa média mais baixa que o baseline**
   (0,1543 vs. 0,1811) mas o **regret médio mais baixo** dos três
   (0,024970, contra 0,026769 do baseline e 0,029457 do LinUCB) — o que a
   princípio parece contraditório. Isso acontece porque `mean realized reward` é
   uma média sobre desfechos binários já sorteados e fixos no dataset estático
   (`final_reward`, uma realização de Bernoulli, alto ruído amostral por decisão),
   enquanto `regret` é calculado contra o valor **esperado** do braço escolhido sob
   a função de recompensa verdadeira do simulador (`oracle_expected_reward`), não
   contra o resultado sorteado daquela linha específica. Regret médio é, portanto,
   a métrica mais confiável para comparar qualidade de decisão entre políticas
   nesta avaliação — e por ela, Thompson Sampling é a melhor das três, inclusive
   processando o maior número de decisões aceitas (3.520, não uma amostra pequena e
   favorável).

Além disso, vale registrar uma assimetria estrutural entre as políticas que ajuda a
explicar por que o baseline, apesar de não-adaptativo, tem a maior recompensa média
bruta: `BestHistoricalArmPolicy.fit` é ajustado usando a tabela de treino
**inteira** (todas as 20.032 linhas, incluindo o próprio desfecho de cada linha
depois avaliada) antes do replay começar — ou seja, o baseline tem uma vantagem de
retrospecto (*hindsight*) que Thompson Sampling e LinUCB não têm, já que estas
aprendem apenas com o que já viram, linha a linha, dentro do próprio replay,
partindo de um prior (Thompson) ou de uma matriz não-informativa (LinUCB). Isso não
invalida a comparação (o baseline é, por definição, a regra fixa mais informada
possível a partir do histórico — o padrão de mercado contra o qual medir ganho
adaptativo), mas explica por que "recompensa acumulada/média" sozinha favorece o
baseline mesmo quando o regret médio (que usa o valor esperado do ambiente, não o
histórico) mostra Thompson Sampling à frente.

## Justificativa do algoritmo principal: Thompson Sampling contextual

Thompson Sampling (`ThompsonSamplingPolicy`,
`src/bandit_platform/policies/thompson_sampling.py`) foi escolhido como a política
adaptativa principal por equilibrar exploração e explotação **por amostragem da
distribuição posterior** (`Beta(alpha, beta)` por segmento×braço), sem exigir um
parâmetro de exploração ajustado manualmente como o `epsilon` de um
epsilon-greedy. Cada chamada a `select_arm` amostra um valor de conversão esperado
por braço a partir da posterior corrente e escolhe o maior — braços com pouca
informação (posterior larga) naturalmente têm mais chance de serem amostrados com
um valor alto por acaso (exploração automática), enquanto braços já validados
repetidamente (posterior estreita e concentrada em um valor alto) são escolhidos de
forma cada vez mais consistente (explotação automática). Essa propriedade evita o
problema central de heurísticas como epsilon-greedy: não há um hiperparâmetro fixo
de taxa de exploração que precise ser calibrado a mão e que, se mal ajustado,
explora demais (desperdiça decisões em braços já conhecidos como ruins) ou de menos
(fica preso em um ótimo local aprendido cedo). Nos números observados, Thompson
Sampling teve o **menor regret médio por decisão** das três políticas (0,024970),
sustentado sobre o maior volume de decisões aceitas (3.520) — evidência de que a
adaptação da posterior efetivamente aproxima a política do ótimo do ambiente, não
apenas em uma amostra pequena e favorável.

## Justificativa da referência a "Nilos-UCB": por que LinUCB

O edital do desafio menciona uma política de referência chamada **"Nilos-UCB"**.
Após busca na literatura de bandits contextuais e não-contextuais conhecida pela
equipe, **não foi encontrado nenhum algoritmo padrão publicado com esse nome** —
não corresponde a nenhuma variante de UCB (UCB1, UCB1-tuned, LinUCB, KL-UCB, GLM-UCB
etc.) documentada em fontes acadêmicas ou de mercado acessíveis à equipe. Diante
disso, a decisão explícita do time foi tratar "Nilos-UCB" como uma referência
ambígua/não-identificável e cobrir o requisito de "uma política da família UCB" com
**LinUCB (Li et al., 2010 — "A Contextual-Bandit Approach to Personalized News
Article Recommendation")**, implementado em `LinUCBPolicy`
(`src/bandit_platform/policies/linucb.py`). LinUCB cobre o mesmo princípio geral que
qualquer variante de UCB compartilha — um limite de confiança superior sobre uma
estimativa de recompensa, escolhendo o braço que maximiza `estimativa + bônus de
incerteza` — mas com contexto contínuo: por braço, mantém uma regressão ridge
disjunta (`_A`, `_b`) sobre o vetor de features (`featurize`, 16 dimensões: 12
categorias de `job` + `age` normalizada + 3 categorias de `poutcome`) e soma à
predição linear um bônus proporcional a `sqrt(x^T A^-1 x)` (maior incerteza sobre
aquele contexto específico → bônus maior → mais exploração dirigida por contexto,
não apenas por braço). Essa é a mesma justificativa registrada no docstring da
classe (`LinUCBPolicy`) e serve como a evidência de aceite deste ponto do edital.
Nos números observados, LinUCB teve a maior entropia de seleção de braço (1,6940,
mais próxima do teto de ln(6) ≈ 1,7918) — consistente com uma política que segue
explorando ativamente contextos incertos mesmo depois de acumular decisões.

## Tratamento de cold-start

O problema de cold-start em um bandit contextual é: no início, sem nenhuma
observação própria, a política não tem como saber qual braço é melhor para qual
segmento de cliente. A solução ingênua — prior uniforme `Beta(1, 1)` por
segmento×braço em Thompson Sampling — trataria todo braço como igualmente provável
antes de qualquer dado, desperdiçando o sinal já disponível na base histórica da
Etapa 1.

Em vez disso, `ThompsonSamplingPolicy` é inicializado com priors informados por um
modelo de propensão em **PyTorch** (`PropensityModel`, regressão logística de 1
camada linear + sigmoid, `train_propensity_model`,
`src/bandit_platform/policies/warm_start.py`), treinado por 200 épocas
(`epochs=200`, `seed=0`) sobre o `target` real da Etapa 1 usando o mesmo vetor de
features de 16 dimensões (`featurize`). Para cada segmento (`job`),
`compute_segment_priors` usa a propensão prevista pelo modelo (`p_hat`) para gerar
`prior_alpha = p_hat * prior_strength` e `prior_beta = (1 - p_hat) * prior_strength`,
com **`prior_strength = 4.0`** — o valor exato usado na execução deste relatório.
Isso equivale a dizer que, antes de qualquer decisão real da Etapa 3, cada
segmento já entra na simulação com o equivalente a **4 pseudo-eventos observados**
(a soma `alpha + beta` de uma posterior Beta é literalmente a contagem efetiva de
observações "vistas"), distribuídos proporcionalmente à propensão de conversão
prevista pelo modelo para aquele segmento — um cold-start informado, não um prior
neutro, mas também não tão forte a ponto de travar a política contra o que os
dados reais da Etapa 3 mostrarem depois (4 pseudo-observações são superadas depois
de poucas dezenas de atualizações reais por segmento×braço).

## Tratamento de recompensas atrasadas

Nesta avaliação offline, a política só aprende com eventos cujo `final_reward` já
está **resolvido** — presente em `delayed_rewards.csv` (Etapa 2), que existe
apenas para os eventos que engajaram (`intermediate_reward == 1`). O join em
`build_training_table` (`src/bandit_platform/evaluation/dataset.py`) usa `how="inner"`
contra `delayed_rewards.csv`, então os eventos com `intermediate_reward == 0` (que
nunca geraram linha em `delayed_rewards.csv`, porque `simulate_delayed_rewards` só
processa `events.loc[events["intermediate_reward"] == 1]`) simplesmente não entram
na tabela de treino/avaliação — de 41.188 eventos totais, ficam de fora os que não
engajaram, restando as 20.032 linhas efetivamente usadas.

Isso é uma **simplificação deliberada da avaliação offline**: o dataset estático já
tem todos os atrasos resolvidos (`delay_days` entre 1 e 14 dias, já sorteado e
fixo) no momento em que o replay roda, então não existe, nesta etapa, nenhuma noção
de "aguardar" um resultado — o resultado já existe na tabela antes da primeira
linha ser processada. Um sistema online real não teria esse luxo: a decisão de
mostrar um braço a um cliente acontece em um instante, e a conversão (ou não) só é
conhecida dias depois, se é que ocorre.

Em produção, o tratamento correto seria manter um **buffer de decisões pendentes
indexado por `event_id`**: no momento em que a política escolhe um braço para um
cliente, a decisão entra no buffer com o contexto, o braço escolhido e um
timestamp; `policy.update(...)` **não** é chamado nesse momento. O buffer é
consultado continuamente (ou por um job periódico) e, para cada decisão pendente,
duas coisas podem acontecer: (1) chega um evento de conversão associado àquele
`event_id` antes do horizonte de 14 dias — a decisão é removida do buffer e
`policy.update(...)` é chamado com a recompensa final observada (1) e o contexto
original; ou (2) o horizonte de 14 dias expira sem conversão — a decisão também é
removida do buffer, mas `policy.update(...)` é chamado com recompensa 0, tratando o
silêncio prolongado como uma conversão negativa implícita, para que a política não
fique com decisões eternamente "em aberto" e continue aprendendo mesmo de braços
que não convertem. Esse buffer e sua lógica de timeout **não foram implementados
como código nesta etapa** — são descritos aqui em texto, o que é exatamente o que a
evidência de aceite do edital pede para este ponto ("tratamento... descrito").

## Limitações e riscos

- **O oráculo usado para calcular regret conhece os parâmetros reais de geração da
  Etapa 2** (`ARM_CONVERSION_EFFECT` e `CHANNEL_ENGAGEMENT_RATE`,
  `src/bandit_platform/synthetic/events.py`) — `run_replay_simulation`
  (`src/bandit_platform/evaluation/simulate.py`) importa esses dicionários
  diretamente e os passa como argumentos para `oracle_expected_reward`
  (`src/bandit_platform/evaluation/metrics.py`). Isso é intencional: em qualquer benchmark de bandit, a avaliação
  precisa de acesso privilegiado à função de recompensa verdadeira do ambiente
  simulado para poder calcular regret — a própria política avaliada nunca vê esses
  valores. Mas isso também significa que o regret medido aqui **não poderia ser
  calculado em produção real**, porque lá a função de recompensa verdadeira (a
  probabilidade real de conversão de cada cliente para cada oferta) é justamente o
  que se está tentando descobrir, não um dado conhecido a priori. Em produção, o
  substituto prático de "regret" é acompanhar a taxa de conversão realizada ao
  longo do tempo e compará-la com a de um grupo de controle/holdout, não um regret
  contra um oráculo inexistente.
- **A taxa de aceitação baixa (~16-18%) do replay com rejeição** limita o tamanho
  efetivo da amostra de avaliação a cerca de 1/6 do total de eventos com recompensa
  resolvida — com mais braços no catálogo, essa taxa cairia ainda mais (proporcional
  a `1/número de braços` sob logging uniforme), tornando o método caro em dados
  quanto mais rica for a política de decisão.
- **Vantagem de retrospecto do baseline**: como descrito na seção de comparação
  quantitativa, `BestHistoricalArmPolicy` é ajustado sobre a tabela de treino
  inteira antes do replay, enquanto Thompson Sampling e LinUCB aprendem apenas
  online, linha a linha, dentro do próprio replay — isso favorece a recompensa
  bruta acumulada/média do baseline e deve ser levado em conta ao interpretar a
  tabela de comparação (regret médio, calculado contra o valor esperado do
  ambiente e não contra o histórico, é a métrica mais robusta a essa assimetria).
- **Ruído amostral em recompensa binária**: `final_reward` é uma única realização
  de Bernoulli por evento (não uma probabilidade), então `cumulative reward` e
  `mean realized reward` têm variância inerente por decisão — regret médio
  (calculado sobre o valor esperado, não sobre o sorteio realizado) é a métrica com
  menos ruído para comparar políticas nesta avaliação.
