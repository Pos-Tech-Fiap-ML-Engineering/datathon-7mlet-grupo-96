# Script de demonstração ao vivo

## Cenário

Demonstração de ~2,5 minutos dentro do pitch de 10 minutos, mostrando o
sistema rodando localmente (não depende de nenhum deploy Azure real, que
ainda não foi aplicado).

## Sequência (ambiente local, `make setup` já executado)

1. `make serve` (outro terminal) — sobe a API em `localhost:8000`.
2. Mostrar uma decisão via CLI:
   ```bash
   .venv/bin/bandit-cli decide --context '{"job":"admin.","age":35,"poutcome":"nonexistent","default":"no","previous":2}'
   ```
   Apontar `arm_id`, `reason_code`, `policy_version` na saída.
3. `make demo` (outro terminal) — sobe o Streamlit em `localhost:8501`.
4. Na aba de decisão do Streamlit, repetir um contexto parecido, mostrar a
   resposta na interface.
5. Na aba do assistente, perguntar algo como "por que o cliente com
   `default=yes` não pode receber CDB?" — mostrar a resposta com fontes
   citadas (RAG).
6. Na aba de auditoria, mostrar o log de decisões acumulado.
7. (Opcional, se o tempo permitir) `bandit-cli policy-status` para mostrar
   a versão ativa e o histórico do registro.

## Plano de contingência

| Falha | Ação |
|---|---|
| Streamlit não sobe a tempo | Seguir só com a CLI (`bandit-cli decide`), que não depende de nenhum servidor além de si mesma |
| API Anthropic indisponível/sem chave configurada | Pular a aba do assistente RAG; mencionar verbalmente a resposta já documentada em `docs/mlops-lifecycle.md`/README |
| Sem internet no local da apresentação | Toda a demonstração roda 100% local (dados já processados versionados, nenhuma chamada de rede exceto ao assistente RAG) — só o passo 5 é afetado, pular como acima |
| Terminal/ambiente quebrado no dia | Ter um terminal de backup já com `.venv` ativado e `make serve`/`make demo` já testados antes da apresentação |

## Gravação (opcional, pontuação extra)

Se o grupo optar por gravar a demonstração: o arquivo de vídeo NÃO deve ser
commitado no repositório (mesma regra de "sem binários grandes" da
Etapa 0) — hospedar externamente (ex.: link não-listado) e referenciar o
link neste arquivo antes do Demo Day, junto com uma descrição textual do
que a gravação mostra, para o caso de o link expirar.
