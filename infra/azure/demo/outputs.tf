output "url" {
  value = "https://${azurerm_container_app.gateway.ingress[0].fqdn}/docs"
}

output "resource_group" {
  value = azurerm_resource_group.demo.name
}
