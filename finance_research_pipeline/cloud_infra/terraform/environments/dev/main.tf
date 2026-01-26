# Resource Group
resource "azurerm_resource_group" "main" {
  name     = "${var.project_name}-rg-${var.environment}"
  location = var.location

  tags = local.tags
}

# Local values
locals {
  tags = merge(var.tags, {
    environment = var.environment
    project     = var.project_name
    managed_by  = "terraform"
  })
}

# Monitoring Module
module "monitoring" {
  source = "../../modules/monitoring"

  project_name        = var.project_name
  environment         = var.environment
  location            = var.location
  resource_group_name = azurerm_resource_group.main.name
  log_retention_days  = 30

  tags = local.tags
}

# Container Registry Module
module "acr" {
  source = "../../modules/acr"

  project_name        = var.project_name
  environment         = var.environment
  location            = var.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "Basic"

  tags = local.tags
}

# Redis Cache Module
module "redis" {
  source = "../../modules/redis"

  project_name        = var.project_name
  environment         = var.environment
  location            = var.location
  resource_group_name = azurerm_resource_group.main.name
  capacity            = 0
  family              = "C"
  sku_name            = "Basic"

  tags = local.tags
}

# Cosmos DB Module
module "cosmos_db" {
  source = "../../modules/cosmos_db"

  project_name        = var.project_name
  environment         = var.environment
  location            = var.location
  resource_group_name = azurerm_resource_group.main.name
  database_name       = "finance_research"

  tags = local.tags
}

# Container Apps Module
module "container_apps" {
  source = "../../modules/container_apps"

  project_name               = var.project_name
  environment                = var.environment
  location                   = var.location
  resource_group_name        = azurerm_resource_group.main.name
  log_analytics_workspace_id = module.monitoring.log_analytics_workspace_id

  # ACR settings
  acr_login_server   = module.acr.login_server
  acr_admin_username = module.acr.admin_username
  acr_admin_password = module.acr.admin_password

  # Container settings
  backend_image_tag  = var.backend_image_tag
  frontend_image_tag = var.frontend_image_tag

  # LLM settings
  azure_openai_endpoint        = var.azure_openai_endpoint
  azure_openai_api_key         = var.azure_openai_api_key
  azure_openai_deployment_name = var.azure_openai_deployment_name

  # Tool API keys
  tavily_api_key = var.tavily_api_key
  newsapi_key    = var.newsapi_key

  # Redis settings
  redis_host     = module.redis.hostname
  redis_password = module.redis.primary_access_key

  # Cosmos DB settings
  cosmos_endpoint = module.cosmos_db.endpoint
  cosmos_key      = module.cosmos_db.primary_key

  # CORS
  cors_origins = ["https://${module.container_apps.frontend_fqdn}"]

  tags = local.tags

  depends_on = [
    module.acr,
    module.redis,
    module.cosmos_db,
    module.monitoring
  ]
}
