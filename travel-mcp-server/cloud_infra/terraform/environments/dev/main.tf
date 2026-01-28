# Local variables
locals {
  resource_prefix = "${var.project_name}-${var.environment}"
  acr_name        = replace("${var.project_name}${var.environment}acr", "-", "")
}

# =============================================================================
# RESOURCE GROUP
# =============================================================================
module "resource_group" {
  source = "../../modules/resource_group"

  name     = "${local.resource_prefix}-rg"
  location = var.location
  tags     = var.tags
}

# =============================================================================
# LOG ANALYTICS
# =============================================================================
module "log_analytics" {
  source = "../../modules/log_analytics"

  name                = "${local.resource_prefix}-logs"
  resource_group_name = module.resource_group.name
  location            = module.resource_group.location
  retention_in_days   = 30
  tags                = var.tags
}

# =============================================================================
# CONTAINER REGISTRY
# =============================================================================
module "acr" {
  source = "../../modules/acr"

  name                = local.acr_name
  resource_group_name = module.resource_group.name
  location            = module.resource_group.location
  sku                 = "Basic"
  admin_enabled       = true
  tags                = var.tags
}

# =============================================================================
# REDIS CACHE
# =============================================================================
module "redis" {
  source = "../../modules/redis"

  name                = "${local.resource_prefix}-redis"
  resource_group_name = module.resource_group.name
  location            = module.resource_group.location
  capacity            = 0
  family              = "C"
  sku_name            = "Basic"
  tags                = var.tags
}

# =============================================================================
# CONTAINER APPS ENVIRONMENT
# =============================================================================
module "container_apps_env" {
  source = "../../modules/container_apps_env"

  name                       = "${local.resource_prefix}-env"
  resource_group_name        = module.resource_group.name
  location                   = module.resource_group.location
  log_analytics_workspace_id = module.log_analytics.id
  tags                       = var.tags
}

# =============================================================================
# AI FOUNDRY (GPT-4o-mini)
# =============================================================================
module "ai_foundry" {
  source = "../../modules/ai_foundry"

  name                  = "${local.resource_prefix}-ai"
  resource_group_name   = module.resource_group.name
  location              = var.ai_foundry_location
  custom_subdomain_name = "${local.resource_prefix}-ai"

  model_deployment_name = "gpt-4o-mini"
  model_name            = "gpt-4o-mini"
  model_version         = "2024-07-18"
  deployment_capacity   = 10

  tags = var.tags
}

# =============================================================================
# BACKEND CONTAINER APP
# =============================================================================
module "backend" {
  source = "../../modules/container_app"

  name                         = "${local.resource_prefix}-backend"
  resource_group_name          = module.resource_group.name
  container_app_environment_id = module.container_apps_env.id

  container_name = "backend"
  image          = "${module.acr.login_server}/travel-mcp-backend:latest"
  cpu            = var.backend_cpu
  memory         = var.backend_memory

  ingress_enabled     = true
  ingress_external    = true
  ingress_target_port = 8000

  env_vars = [
    { name = "REDIS_HOST", value = module.redis.hostname },
    { name = "REDIS_PORT", value = "6380" },
    { name = "AZURE_AI_ENDPOINT", value = module.ai_foundry.endpoint },
    { name = "AZURE_AI_MODEL", value = module.ai_foundry.model_deployment_name },
  ]

  secret_env_vars = [
    { name = "REDIS_PASSWORD", secret_name = "redis-password" },
    { name = "SERPAPI_API_KEY", secret_name = "serpapi-key" },
    { name = "OPENWEATHER_API_KEY", secret_name = "openweather-key" },
    { name = "GOOGLE_PLACES_API_KEY", secret_name = "google-places-key" },
    { name = "EXCHANGERATE_API_KEY", secret_name = "exchangerate-key" },
    { name = "AZURE_AI_KEY", secret_name = "azure-ai-key" },
  ]

  secrets = [
    { name = "redis-password", value = module.redis.primary_access_key },
    { name = "serpapi-key", value = var.serpapi_api_key },
    { name = "openweather-key", value = var.openweather_api_key },
    { name = "google-places-key", value = var.google_places_api_key },
    { name = "exchangerate-key", value = var.exchangerate_api_key },
    { name = "azure-ai-key", value = module.ai_foundry.primary_access_key },
    { name = "acr-password", value = module.acr.admin_password },
  ]

  registry_server               = module.acr.login_server
  registry_username             = module.acr.admin_username
  registry_password_secret_name = "acr-password"

  tags = var.tags
}

# =============================================================================
# FRONTEND CONTAINER APP
# =============================================================================
module "frontend" {
  source = "../../modules/container_app"

  name                         = "${local.resource_prefix}-frontend"
  resource_group_name          = module.resource_group.name
  container_app_environment_id = module.container_apps_env.id

  container_name = "frontend"
  image          = "${module.acr.login_server}/travel-mcp-frontend:latest"
  cpu            = var.frontend_cpu
  memory         = var.frontend_memory

  ingress_enabled     = true
  ingress_external    = true
  ingress_target_port = 80

  env_vars = [
    { name = "VITE_API_URL", value = module.backend.url },
  ]

  secrets = [
    { name = "acr-password", value = module.acr.admin_password },
  ]

  registry_server               = module.acr.login_server
  registry_username             = module.acr.admin_username
  registry_password_secret_name = "acr-password"

  tags = var.tags

  depends_on = [module.backend]
}
