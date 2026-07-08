# Slide 1: Plataforma de Experimentação Adaptativa

Datathon 7MLET — Grupo 96

Multi-armed bandit contextual para decisão de oferta/mensagem/canal em
canais digitais de uma instituição financeira.

# Slide 2: O problema

- Regras fixas e testes A/B longos desperdiçam tráfego
- Demoram a reagir a mudanças de contexto
- Dificultam personalização responsável
- Solução: bandit contextual com exploração/explotação balanceadas

# Slide 3: Abordagem algorítmica

- Baseline determinístico (controle)
- Thompson Sampling (Beta-Bernoulli + warm-start via PyTorch)
- LinUCB (Li et al. 2010) — resposta à família UCB do edital
- "Nilos-UCB" não localizado na literatura — substituição justificada

# Slide 4: Dados

- Kaggle bank-marketing (henriqueyamahata, CC0), 41.188 linhas
- `duration` removida por vazamento temporal
- Camada sintética de enriquecimento, fisicamente separada da base original
- Golden set: 22 casos curados, 4 categorias, 12 segmentos cobertos

# Slide 5: Resultados quantitativos

- Regret medio/decisao: baseline 0.026769, Thompson Sampling 0.024970 (melhor), LinUCB 0.029457
- Golden-set safety rate: 100% nas tres politicas
- Fairness de exposicao: 13,6%-18,7% (teorico uniforme: 16,7%)

# Slide 6: Demonstração ao vivo

- API `/decide` + CLI `bandit-cli decide`
- Interface Streamlit (decisão, assistente RAG, auditoria)
- Assistente com LLM: resume experimentos, explica decisões, recupera política interna

# Slide 7: Governança — Model Card e System Card

- Uso pretendido e fora de escopo declarados
- 4 cenários de risco documentados (reward hacking, manipulação de contexto, abuso do assistente, violação de suitability)
- Guard de suitability cobre apenas 2 das regras de negócio documentadas — lacuna registrada, não escondida

# Slide 8: Ciclo de vida MLOps

- Registro de políticas versionado, com aprovação humana estruturada
- Critérios de promoção objetivos (safety, regret absoluto, não-regressão)
- Rollback com histórico completo
- Passeio guiado real: 1 hipótese formalizada, 1 rejeitada, 1 promovida e revertida

# Slide 9: Arquitetura-alvo Azure

- Exclusivamente Azure: Container Apps, Blob Storage, Key Vault + Managed Identity, Log Analytics
- Terraform completo (`init`/`validate` reais); `apply` pendente de credenciais
- Alternativas descartadas: Azure Container Registry (custo fixo), App Service dedicado (custo ocioso)

# Slide 10: FinOps

- Custo estimado: ~US$5-10/mes
- Orcamento real via Terraform: US$20/mes, alerta em 80%
- Container Apps com scale-to-zero: custo de computo tende a zero sem trafego

# Slide 11: Cenários de escala e redução

- Aumento de trafego: `max_replicas` sobe sem mudanca de arquitetura
- Reducao adicional: retencao de Log Analytics, tiers frios de Blob
- Sem uso: custo de computo proximo de zero via `min_replicas=0`

# Slide 12: Limitações e riscos

- Apenas 2 das regras de suitability documentadas ainda foram codificadas
- Sem loop de recompensa real em producao
- Golden set curado, nao amostrado estatisticamente

# Slide 13: Impacto e próximos passos

- Metodologia end-to-end demonstrada: dados -> bandit -> avaliacao -> servico -> MLOps -> governanca
- Proximos passos: completar guard de suitability, conectar recompensa real, agendar monitoramento de drift

# Slide 14: Obrigado

Perguntas?
