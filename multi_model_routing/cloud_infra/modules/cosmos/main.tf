terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}

variable "resource_group_name" {
  type        = string
  description = "Resource group name"
}

variable "location" {
  type        = string
  description = "Azure region"
}

variable "resource_prefix" {
  type        = string
  description = "Prefix for resource names"
}

variable "tags" {
  type        = map(string)
  description = "Resource tags"
}

variable "throughput" {
  type        = number
  default     = 400
  description = "Request units per second"
}

# Cosmos DB Account
resource "azurerm_cosmosdb_account" "main" {
  name                = "${var.resource_prefix}-cosmos"
  location            = var.location
  resource_group_name = var.resource_group_name
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"
  tags                = var.tags

  # Enable free tier for dev (1000 RU/s, 25GB)
  free_tier_enabled = true

  consistency_policy {
    consistency_level = "Session"
  }

  geo_location {
    location          = var.location
    failover_priority = 0
  }

  capabilities {
    name = "EnableServerless"
  }
}

# Database
resource "azurerm_cosmosdb_sql_database" "main" {
  name                = "llm_routing"
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.main.name
}

# Container: routing_logs
resource "azurerm_cosmosdb_sql_container" "routing_logs" {
  name                = "routing_logs"
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.main.name
  database_name       = azurerm_cosmosdb_sql_database.main.name
  partition_key_paths = ["/user_id"]

  indexing_policy {
    indexing_mode = "consistent"

    included_path {
      path = "/*"
    }

    excluded_path {
      path = "/\"_etag\"/?"
    }
  }

  # TTL for automatic cleanup (90 days)
  default_ttl = 7776000
}

# Container: budgets
resource "azurerm_cosmosdb_sql_container" "budgets" {
  name                = "budgets"
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.main.name
  database_name       = azurerm_cosmosdb_sql_database.main.name
  partition_key_paths = ["/user_id"]

  indexing_policy {
    indexing_mode = "consistent"

    included_path {
      path = "/*"
    }
  }
}

# Container: analytics_aggregates
resource "azurerm_cosmosdb_sql_container" "analytics" {
  name                = "analytics_aggregates"
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.main.name
  database_name       = azurerm_cosmosdb_sql_database.main.name
  partition_key_paths = ["/date"]

  indexing_policy {
    indexing_mode = "consistent"

    included_path {
      path = "/*"
    }
  }
}

output "endpoint" {
  value = azurerm_cosmosdb_account.main.endpoint
}

output "primary_key" {
  value     = azurerm_cosmosdb_account.main.primary_key
  sensitive = true
}

output "connection_string" {
  value     = azurerm_cosmosdb_account.main.primary_sql_connection_string
  sensitive = true
}

output "database_name" {
  value = azurerm_cosmosdb_sql_database.main.name
}
