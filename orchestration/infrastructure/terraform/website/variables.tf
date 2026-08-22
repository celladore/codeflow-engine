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
  default     = "cel-prod-codeflow-rg"
}

variable "location" {
  description = "Azure region for the Static Web App. Static Web Apps support a limited region set."
  type        = string
  default     = "eastus2"
}

variable "static_web_app_name" {
  description = "Azure Static Web App resource name."
  type        = string
  default     = "cel-prod-codeflow-swa"
}

variable "custom_domain" {
  description = "Codeflow launch domain. DNS CNAME is owned by celladore-org/infrastructure/dns (Cloudflare, zone celladoresystems.com)."
  type        = string
  default     = "codeflow.celladoresystems.com"
}

variable "enable_custom_domain" {
  description = "Enable only after celladore-org/infrastructure/dns has created the CNAME to the Static Web App default hostname and it resolves. Live reality as of 2026-08-19: the CNAME resolves and the custom domain is bound (done directly via `az staticwebapp hostname set`, not through this stack — see README's known-gap note). Default reflects that; a real first apply still needs the SWA imported first or this will try to create a duplicate."
  type        = bool
  default     = true
}

variable "sku_tier" {
  description = "Static Web App SKU tier. Live resource is Free (confirmed supports up to 2 custom domains, which covers this use case) — departs from this stack's original Standard default."
  type        = string
  default     = "Free"
}

variable "sku_size" {
  description = "Static Web App SKU size."
  type        = string
  default     = "Free"
}

variable "tags" {
  description = "Tags applied to website resources."
  type        = map(string)
  default = {
    Environment = "Production"
    Product     = "Codeflow"
    Owner       = "celladore"
    ManagedBy   = "Terraform"
  }
}
