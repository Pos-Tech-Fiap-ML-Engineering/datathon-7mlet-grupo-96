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
