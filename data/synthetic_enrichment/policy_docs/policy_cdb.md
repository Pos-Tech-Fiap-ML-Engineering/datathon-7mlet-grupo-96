# Política Comercial — CDB Prazo Fixo (sintético/fictício)

Este documento é fictício, criado para fins de demonstração do Datathon 7MLET.

## Elegibilidade

- Cliente deve ter idade mínima de 18 anos.
- Cliente com `default = yes` (crédito em default) não é elegível para nenhuma
  variante de CDB — risco de crédito incompatível com o produto.
- Clientes com `poutcome = failure` em campanha anterior podem ser reofertados,
  mas com prioridade reduzida na exploração (ver `suitability_geral.md`).

## Suitability

- CDB 24 meses (`cdb_24m`) só deve ser ofertado a clientes que já demonstraram
  algum engajamento prévio (contato anterior com `previous > 0`), pois exige
  maior comprometimento de prazo.
- CDB 12 meses (`cdb_12m`) é o produto de entrada, adequado a qualquer cliente
  elegível.
- Aviso de taxa promocional (`taxa_promocional`) tem validade de 30 dias
  corridos a partir da geração do evento; após esse prazo, a oferta não deve
  mais ser exibida.

## Observações de compliance

- Nenhuma comunicação pode prometer rentabilidade garantida acima da taxa
  contratual informada no momento da oferta.
