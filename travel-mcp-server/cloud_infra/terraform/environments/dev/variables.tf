variable "subscription_id" {
  description = "Azure subscription ID"
  type        = string
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "travel-mcp"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "eastus"
}

variable "ai_foundry_location" {
  description = "Azure region for AI Foundry (OpenAI models)"
  type        = string
  default     = "eastus2"
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Project     = "travel-mcp-server"
    Environment = "dev"
    ManagedBy   = "terraform"
  }
}

# API Keys (sensitive)
variable "serpapi_api_key" {
  description = "SerpAPI key for flight/hotel search"
  type        = string
  sensitive   = true
  default     = ""
}

variable "openweather_api_key" {
  description = "OpenWeather API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "google_places_api_key" {
  description = "Google Places API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "exchangerate_api_key" {
  description = "ExchangeRate API key"
  type        = string
  sensitive   = true
  default     = ""
}

# Container configuration
variable "backend_cpu" {
  description = "CPU cores for backend container"
  type        = number
  default     = 0.5
}

variable "backend_memory" {
  description = "Memory in GB for backend container"
  type        = string
  default     = "1Gi"
}

variable "frontend_cpu" {
  description = "CPU cores for frontend container"
  type        = number
  default     = 0.25
}

variable "frontend_memory" {
  description = "Memory in GB for frontend container"
  type        = string
  default     = "0.5Gi"
}
