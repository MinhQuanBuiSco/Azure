# General Configuration
resource_group_name = "rg-rag-app-prod"
location            = "eastus2"

tags = {
  Environment = "Production"
  Application = "RAG-App"
  ManagedBy   = "Terraform"
  CostCenter  = "Engineering"
}

# Storage Account (must be globally unique, lowercase, no hyphens)
storage_account_name = "stragapp20250112"
blob_container_name  = "pdfs"

# Redis Cache (must be globally unique)
redis_cache_name = "redis-rag-app-20250112"
redis_sku        = "Standard"
redis_capacity   = 1  # C1 (1GB)

# Azure AI Search (must be globally unique)
search_service_name   = "srch-rag-app-20250112"
search_sku            = "standard"
search_replica_count  = 1
search_partition_count = 1
search_index_name     = "rag-index"

# Azure OpenAI (must be globally unique)
openai_name     = "openai-rag-app-20250112"
openai_location = "eastus"  # Check availability
openai_sku      = "S0"

# OpenAI Chat Model (GPT-4o-mini)
openai_chat_deployment_name = "gpt-4o-mini"
openai_chat_model           = "gpt-4o-mini"
openai_chat_model_version   = "2024-07-18"
openai_chat_capacity        = 30  # 30K TPM

# OpenAI Embedding Model
openai_embedding_deployment_name = "text-embedding-3-small"
openai_embedding_model           = "text-embedding-3-small"
openai_embedding_model_version   = "1"
openai_embedding_capacity        = 120  # 120K TPM

# Container Registry (must be globally unique, alphanumeric only)
acr_name          = "acrragapp20250112"
acr_sku           = "Standard"
acr_admin_enabled = true

# Container Apps
container_apps_env_name = "cae-rag-app-prod"
backend_app_name        = "ca-rag-backend"
backend_image_name      = "rag-backend"
backend_image_tag       = "latest"
backend_cpu             = 1.0
backend_memory          = "2Gi"
backend_min_replicas    = 3
backend_max_replicas    = 50

# Static Web App
static_web_app_name     = "swa-rag-frontend-20250112"
static_web_app_location = "eastus2"
static_web_app_sku      = "Standard"

# Application Insights
app_insights_name = "appi-rag-app-prod"
