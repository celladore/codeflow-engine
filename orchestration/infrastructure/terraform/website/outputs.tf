output "resource_group_name" {
  description = "Codeflow website resource group."
  value       = azurerm_resource_group.website.name
}

output "static_web_app_name" {
  description = "Codeflow Static Web App resource name."
  value       = azurerm_static_web_app.website.name
}

output "static_web_app_default_hostname" {
  description = "Default hostname to pass to celladore-org/infrastructure/dns as the codeflow CNAME target."
  value       = azurerm_static_web_app.website.default_host_name
}

output "static_web_app_api_key" {
  description = "Deployment API key for the Codeflow website deploy workflow."
  value       = azurerm_static_web_app.website.api_key
  sensitive   = true
}

output "custom_domain" {
  description = "Configured Codeflow launch domain."
  value       = var.custom_domain
}
