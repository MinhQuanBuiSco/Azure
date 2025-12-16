output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

output "resource_group_location" {
  description = "Location of the resource group"
  value       = azurerm_resource_group.main.location
}

# ACR Outputs
output "acr_login_server" {
  description = "Login server for Azure Container Registry"
  value       = module.acr.acr_login_server
}

output "acr_name" {
  description = "Name of the Azure Container Registry"
  value       = module.acr.acr_name
}

# AKS Outputs
output "aks_cluster_name" {
  description = "Name of the AKS cluster"
  value       = module.aks.cluster_name
}

output "aks_cluster_id" {
  description = "ID of the AKS cluster"
  value       = module.aks.cluster_id
}

output "get_aks_credentials_command" {
  description = "Command to get AKS credentials"
  value       = "az aks get-credentials --resource-group ${azurerm_resource_group.main.name} --name ${module.aks.cluster_name}"
}

# Azure OpenAI Outputs - COMMENTED OUT (using regular OpenAI API instead)
# output "openai_endpoint" {
#   description = "Endpoint for Azure OpenAI service"
#   value       = module.openai.openai_endpoint
# }
#
# output "openai_deployment_name" {
#   description = "Name of the OpenAI model deployment"
#   value       = module.openai.deployment_name
# }
#
# output "openai_primary_key" {
#   description = "Primary access key for Azure OpenAI (sensitive)"
#   value       = module.openai.openai_primary_key
#   sensitive   = true
# }

# Summary output with all important information
output "deployment_summary" {
  description = "Summary of deployed resources"
  value = <<-EOT

  ===================================
  Azure Chatbot Deployment Summary
  ===================================

  Resource Group: ${azurerm_resource_group.main.name}
  Location: ${azurerm_resource_group.main.location}

  Container Registry:
    - Login Server: ${module.acr.acr_login_server}
    - Login Command: az acr login --name ${module.acr.acr_name}

  Kubernetes Cluster:
    - Cluster Name: ${module.aks.cluster_name}
    - Get Credentials: az aks get-credentials --resource-group ${azurerm_resource_group.main.name} --name ${module.aks.cluster_name}

  AI Service:
    - Using regular OpenAI API (not Azure OpenAI due to quota limits)
    - Set OPENAI_API_KEY in backend/.env file
    - Sign up at: https://platform.openai.com/api-keys

  Next Steps:
    1. Get AKS credentials: Run the command above
    2. Login to ACR: az acr login --name ${module.acr.acr_name}
    3. Get OpenAI API key from platform.openai.com
    4. Build and push Docker images
    5. Deploy to Kubernetes

  EOT
}
