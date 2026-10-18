variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "devhub-464904"
}

variable "region" {
  description = "GCP Region for Cloud SQL"
  type        = string
  default     = "asia-northeast1"
}

variable "tier" {
  description = "Cloud SQL Instance Tier (2 vCPU, 7.5GB RAM for fast provisioning)"
  type        = string
  default     = "db-custom-2-7680"
}

variable "db_version" {
  description = "PostgreSQL Major Version"
  type        = string
  default     = "POSTGRES_13"
}
