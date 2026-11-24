# Public demo of the gateway on Azure Container Apps. Scales to zero, so an idle
# demo bills nothing. Separate from ../main.tf, whose Premium registry and Key
# Vault are the enterprise design and are not needed to run the demo.

terraform {
  required_version = ">= 1.6"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.100"
    }
  }
}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "demo" {
  name     = "rg-${var.prefix}-demo"
  location = var.location
  tags     = var.tags
}

resource "azurerm_log_analytics_workspace" "demo" {
  name                = "log-${var.prefix}-demo"
  location            = azurerm_resource_group.demo.location
  resource_group_name = azurerm_resource_group.demo.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = var.tags
}

resource "azurerm_container_app_environment" "demo" {
  name                       = "cae-${var.prefix}-demo"
  location                   = azurerm_resource_group.demo.location
  resource_group_name        = azurerm_resource_group.demo.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.demo.id
  tags                       = var.tags
}

resource "azurerm_container_app" "gateway" {
  name                         = "ca-${var.prefix}-gateway"
  container_app_environment_id = azurerm_container_app_environment.demo.id
  resource_group_name          = azurerm_resource_group.demo.name
  revision_mode                = "Single"
  tags                         = var.tags

  template {
    min_replicas = 0
    max_replicas = 1

    container {
      name   = "gateway"
      image  = var.image
      cpu    = 0.25
      memory = "0.5Gi"

      env {
        name  = "gateway-rate-limit-per-minute"
        value = "30"
      }

      env {
        name  = "gateway-max-prompt-chars"
        value = "4000"
      }
    }

    # Cap parallel work on the single replica so a burst cannot fan out cost.
    http_scale_rule {
      name                = "http-concurrency"
      concurrent_requests = "10"
    }
  }

  ingress {
    external_enabled = true
    target_port      = 7860
    transport        = "http"

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }
}
