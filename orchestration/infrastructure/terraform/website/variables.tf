variable "subscription_id" {
  description = "Azure subscription ID for Codeflow website infrastructure."
  type        = string
}

variable "tenant_id" {
  description = "Azure tenant ID for Codeflow website infrastructure."
  type        = string
}

variable "resource_group_name" {
  description = "Resource group for Codeflow website hosting."
  type        = string
  default     = "pvc-prod-codeflow-rg"
}

variable "location" {
  description = "Azure region for the Static Web App. Static Web Apps support a limited region set."
  type        = string
  default     = "eastus2"
}

variable "static_web_app_name" {
  description = "Azure Static Web App resource name."
  type        = string
  default     = "pvc-prod-codeflow-swa"
}

variable "custom_domain" {
  description = "Codeflow launch domain. DNS CNAME is owned by celladore-org/infrastructure/dns (Cloudflare, zone celladoresystems.com)."
  type        = string
  default     = "codeflow.celladoresystems.com"
}

variable "enable_custom_domain" {
  description = "Enable only after celladore-org/infrastructure/dns has created the CNAME to the Static Web App default hostname and it resolves."
  type        = bool
  default     = false
}

variable "sku_tier" {
  description = "Static Web App SKU tier."
  type        = string
  default     = "Standard"
}

variable "sku_size" {
  description = "Static Web App SKU size."
  type        = string
  default     = "Standard"
}

variable "tags" {
  description = "Tags applied to website resources."
  type        = map(string)
  default = {
    Environment = "Production"
    Product     = "Codeflow"
    Owner       = "phoenixvc"
    ManagedBy   = "Terraform"
  }
}
