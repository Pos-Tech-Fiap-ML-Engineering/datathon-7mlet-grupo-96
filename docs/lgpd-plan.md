# Plano LGPD (Lei Geral de Proteção de Dados)

## Contexto — o que este projeto realmente processa hoje

Este projeto usa **exclusivamente a base pública e anonimizada do Kaggle**
("bank-marketing", henriqueyamahata, licença CC0, derivada do UCI Bank
Marketing Dataset) — **nenhum dado real de cliente identificável é
processado em nenhum momento**. Toda a camada de enriquecimento sintético
(catálogo de ofertas, eventos, recompensas) é gerada por código
determinístico (Etapa 2), não reflete interações reais de clientes.

Este documento tem duas partes, deliberadamente separadas: (1) a
verificação de que o estado atual do projeto não processa dado pessoal
real; (2) o plano de conformidade que **governaria uma implantação real**
desta arquitetura com dados reais de clientes — tratado explicitamente como
desenho prospectivo, não como descrição do sistema hoje.

## Parte 1 — Verificação do estado atual

- **Identificadores**: a base Kaggle não possui coluna de identificador de
  cliente (confirmado em `data/kaggle/README.md`) — linhas duplicadas nem
  sequer podem ser atribuídas a um mesmo cliente real. O `client_context_id`
  sintético usado para juntar eventos/recompensas é um índice de linha
  artificial, nunca exposto pela API.
- **Dados sensíveis (LGPD Art. 5º, II)**: origem racial/étnica, convicção
  religiosa, opinião política, dado de saúde, vida sexual, dado genético/
  biométrico — **nenhuma dessas categorias existe** nas 21 colunas
  processadas (`age, job, marital, education, default, housing, loan,
  contact, month, day_of_week, campaign, pdays, previous, poutcome,
  emp.var.rate, cons.price.idx, cons.conf.idx, euribor3m, nr.employed, y,
  target`) nem no schema da API (`DecisionRequest`: `job, age, poutcome,
  default, previous`).
- **Log de auditoria**: `logs/decisions.jsonl` grava o contexto da decisão
  (5 campos comportamentais não-identificantes) mais um `decision_id`
  (UUID4 interno, chave de correlação da aplicação — não um identificador
  pessoal).
- **Segredos**: `ANTHROPIC_API_KEY`/`KAGGLE_API_TOKEN` ficam em `.env`
  (fora do git, `.gitignore`), nunca commitados; `.env.example` documenta
  as variáveis necessárias sem valores reais.

## Parte 2 — Plano de conformidade para uma implantação real (prospectivo)

### Base legal

Para uma implantação real processando dados de clientes existentes, a base
legal mais provável seria "execução de contrato ou de procedimentos
preliminares relacionados a contrato" (LGPD Art. 7º, V) para a relação já
estabelecida com o cliente. Para prospecção de não-clientes, seria
necessário avaliar "legítimo interesse" (Art. 7º, IX), sempre precedido de
um Teste de Balanceamento de Interesses (LIA) documentado — nunca aplicável
a dado de categoria sensível.

### Finalidade

Exclusivamente a personalização de oferta/mensagem/canal descrita neste
projeto — sem uso secundário (revenda ou compartilhamento de logs de
decisão, uso para scoring de crédito não declarado, ou qualquer finalidade
não comunicada ao titular).

### Minimização

O contrato de API já é minimalista por desenho: `DecisionRequest` aceita
apenas `job, age, poutcome, default, previous` — nenhum nome, CPF,
endereço, telefone, e-mail ou valor financeiro absoluto. Uma implantação
real deveria manter essa mesma disciplina: o serviço de decisão nunca
precisa de mais do que sinais comportamentais agregados no momento da
decisão.

### Mapeamento de identificadores e atributos protegidos

| Campo | Classificação | Observação |
|---|---|---|
| `job`, `poutcome`, `default`, `previous` | Comportamental, não-identificante isoladamente | Já minimizado por desenho |
| `age` | Quase-identificador fraco | Combinado com poucos outros atributos, baixo risco de reidentificação nos volumes tratados |
| `decision_id` | Identificador interno de aplicação | UUID4, não é dado pessoal, é uma chave de correlação técnica |
| Dado sensível (Art. 5º, II) | Não aplicável | Nenhum campo desta categoria existe no sistema |

### Ciclo de retenção

**Gap documentado hoje**: `logs/decisions.jsonl`, `mlruns/` e
`models/registry/` são artefatos locais, ignorados pelo git, sem política
de retenção definida em código. **Desenho para produção real**: logs de
decisão retidos por um prazo definido (ex.: 12-24 meses, a definir com a
área jurídica) para fins de auditoria, depois anonimizados adicionalmente
ou expurgados; metadados do MLflow (hiperparâmetros/métricas, sem dado
pessoal) podem ser retidos indefinidamente; artefatos de política superados
no Policy Registry devem ser podados periodicamente — a poda automática
ainda não existe (ver limitação equivalente em
`docs/mlops-lifecycle.md`).

### Política de logs/telemetria

A arquitetura-alvo Azure (Etapa 6) prevê Application Insights para
telemetria de requisição/exceção/latência. **Requisito de desenho**: a
telemetria nunca deve replicar o payload bruto de `context` — apenas
métricas agregadas/estruturais (latência, contagem, taxa de erro) — para
não duplicar dado comportamental em um segundo sistema com controle de
acesso potencialmente mais amplo. Este requisito ainda não foi
implementado/verificado em código, está registrado aqui como pendência de
hardening antes de qualquer uso real.

### Plano de resposta a incidentes

- **Cenário real do projeto hoje**: o principal risco de incidente é
  exposição das chaves de API em `.env` — já mitigado por mantê-lo fora do
  git e fornecer `.env.example` sem valores reais; em caso de exposição
  acidental, o procedimento é revogar e regerar a chave imediatamente
  (Anthropic/Kaggle) e, na arquitetura-alvo Azure, rotacionar o segredo no
  Key Vault.
- **Procedimento para uma implantação real** (prospectivo): (1) conter —
  revogar credenciais expostas via Key Vault/Managed Identity; (2) avaliar
  escopo usando a trilha do log de auditoria (`decision_id`/`timestamp`);
  (3) notificar a ANPD e os titulares afetados em prazo razoável se
  confirmado risco relevante aos titulares (LGPD Art. 48); (4) documentar o
  incidente e revisar os guardrails que falharam.

## Limitação geral deste plano

Este documento cobre o desenho de conformidade que uma implantação real
exigiria — **não é uma certificação de conformidade**, já que o sistema
atual nunca processa dado pessoal real. Qualquer decisão de levar esta
arquitetura para produção com dados reais exige revisão jurídica formal
antes do primeiro uso.
