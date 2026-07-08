resource "azurerm_consumption_budget_resource_group" "main" {
  name              = "budget-${var.project_name}-${var.environment}"
  resource_group_id = azurerm_resource_group.main.id

  amount     = 20
  time_grain = "Monthly"

  time_period {
    # start_date é obrigatório neste provider (sem default) e precisa ser o
    # primeiro dia de um mês em UTC. Este valor é um placeholder documentado,
    # não um cálculo dinâmico a partir da data atual (evita valores
    # não reprodutíveis) — atualizar para o primeiro dia do mês corrente
    # antes de um `terraform apply` real.
    start_date = "2026-07-01T00:00:00Z"
  }

  notification {
    enabled        = true
    threshold      = 80
    operator       = "GreaterThan"
    threshold_type = "Actual"
    contact_emails = [var.budget_notification_email]
  }
}
