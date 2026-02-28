output "task_api_fqdn" {
  value = azurerm_container_app.task_api.ingress[0].fqdn
}

output "notification_fqdn" {
  value = azurerm_container_app.notification.ingress[0].fqdn
}

output "audit_fqdn" {
  value = azurerm_container_app.audit.ingress[0].fqdn
}

output "task_api_url" {
  value = "https://${azurerm_container_app.task_api.ingress[0].fqdn}"
}

output "notification_url" {
  value = "https://${azurerm_container_app.notification.ingress[0].fqdn}"
}

output "audit_url" {
  value = "https://${azurerm_container_app.audit.ingress[0].fqdn}"
}

output "environment_id" {
  value = azurerm_container_app_environment.this.id
}
