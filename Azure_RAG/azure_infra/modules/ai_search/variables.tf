variable "name" {
  description = "Name of the search service"
  type        = string
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "sku" {
  description = "SKU (free, basic, standard, standard2, standard3, storage_optimized_l1, storage_optimized_l2)"
  type        = string
  default     = "standard"
}

variable "replica_count" {
  description = "Number of replicas"
  type        = number
  default     = 1
}

variable "partition_count" {
  description = "Number of partitions"
  type        = number
  default     = 1
}

variable "tags" {
  description = "Tags to apply"
  type        = map(string)
  default     = {}
}
