variable "project_name" {
  description = "Nome curto do projeto, usado como prefixo dos recursos"
  type        = string
  default     = "banditgrupo96"
}

variable "environment" {
  description = "Ambiente de deploy (ex.: demo, prod)"
  type        = string
  default     = "demo"
}

variable "location" {
  description = "Regiao Azure onde os recursos serao criados"
  type        = string
  default     = "brazilsouth"
}

variable "container_image_api" {
  description = "Imagem da API publicada no GitHub Container Registry (ghcr.io) - evita o custo fixo do Azure Container Registry"
  type        = string
  default     = "ghcr.io/pos-tech-fiap-ml-engineering/datathon-7mlet-grupo-96-api:latest"
}

variable "container_image_streamlit" {
  description = "Imagem do Streamlit publicada no GitHub Container Registry (ghcr.io)"
  type        = string
  default     = "ghcr.io/pos-tech-fiap-ml-engineering/datathon-7mlet-grupo-96-streamlit:latest"
}

variable "anthropic_api_key_secret_name" {
  description = "Nome do segredo no Key Vault que guarda a ANTHROPIC_API_KEY"
  type        = string
  default     = "anthropic-api-key"
}

variable "budget_notification_email" {
  description = "E-mail para notificações do orçamento mensal (definido via .tfvars local, nunca versionado)"
  type        = string
}
