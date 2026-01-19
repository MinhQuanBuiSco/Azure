variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "eastus"
}

# PostgreSQL Variables
variable "postgres_name" {
  description = "Name of PostgreSQL server"
  type        = string
}

variable "postgres_version" {
  description = "PostgreSQL version"
  type        = string
  default     = "15"
}

variable "postgres_admin_username" {
  description = "PostgreSQL admin username"
  type        = string
  default     = "pgadmin"
}

variable "postgres_admin_password" {
  description = "PostgreSQL admin password"
  type        = string
  sensitive   = true
}

variable "postgres_sku" {
  description = "PostgreSQL SKU (B_Standard_B1ms for cost optimization)"
  type        = string
  default     = "B_Standard_B1ms"
}

variable "postgres_storage_mb" {
  description = "PostgreSQL storage in MB"
  type        = number
  default     = 32768
}

variable "database_name" {
  description = "Name of the database"
  type        = string
  default     = "fraud_detection"
}

# Redis Variables
variable "redis_name" {
  description = "Name of Redis cache"
  type        = string
}

variable "redis_sku" {
  description = "Redis SKU (Basic for cost optimization)"
  type        = string
  default     = "Basic"
}

variable "redis_family" {
  description = "Redis family"
  type        = string
  default     = "C"
}

variable "redis_capacity" {
  description = "Redis capacity (0 = 250 MB for Basic)"
  type        = number
  default     = 0
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default = {
    Environment = "development"
    Project     = "fraud-detection"
    ManagedBy   = "terraform"
  }
}

# Production features
variable "high_availability" {
  description = "Enable high availability for PostgreSQL"
  type        = bool
  default     = false
}

variable "backup_retention_days" {
  description = "Backup retention days for PostgreSQL"
  type        = number
  default     = 7
}

variable "geo_redundant_backup" {
  description = "Enable geo-redundant backup for PostgreSQL"
  type        = bool
  default     = false
}

variable "enable_private_endpoints" {
  description = "Enable private endpoints for databases"
  type        = bool
  default     = false
}

variable "subnet_id" {
  description = "Subnet ID for private endpoints"
  type        = string
  default     = ""
}
