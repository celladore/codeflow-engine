variable "subscription_id" {
  description = "Azure subscription ID for Codeflow runtime infrastructure."
  type        = string
}

variable "tenant_id" {
  description = "Azure tenant ID for Codeflow runtime infrastructure."
  type        = string
}

variable "resource_group_name" {
  description = "Existing Codeflow production resource group."
  type        = string
  default     = "cel-prod-codeflow-rg"
}

variable "location" {
  description = "Azure region for Codeflow runtime resources."
  type        = string
  default     = "southafricanorth"
}

variable "container_app_name" {
  description = "Codeflow runtime Container App name."
  type        = string
  default     = "cel-prod-codeflow-api"
}

variable "container_app_environment_name" {
  description = "Codeflow Container Apps Environment name."
  type        = string
  default     = "cel-prod-codeflow-cae"
}

variable "log_analytics_workspace_name" {
  description = "Log Analytics Workspace for Codeflow Container Apps logs."
  type        = string
  default     = "cel-prod-codeflow-law"
}

variable "container_registry_name" {
  description = "Globally unique Azure Container Registry name. ACR names cannot contain dashes."
  type        = string
  default     = "celprodcodeflowacr"
}

variable "container_app_identity_name" {
  description = "User-assigned managed identity attached to the Codeflow Container App."
  type        = string
  default     = "cel-prod-codeflow-api-mi"
}

variable "initial_image" {
  description = "Codeflow Engine image deployed by default. Override only for bootstrap scenarios."
  type        = string
  default     = "celprodcodeflowacr.azurecr.io/codeflow-engine:master"
}

variable "tags" {
  description = "Tags applied to Codeflow runtime resources."
  type        = map(string)
  default = {
    Environment = "prod"
    Product     = "codeflow"
    Owner       = "celladore"
    ManagedBy   = "terraform"
  }
}
