variable "project_id" {
  description = "GCP project ID"
  type        = string
  default     = "devhub-464904"
}

variable "region" {
  description = "GCP region for the VPC subnet and both reserved IPs"
  type        = string
  default     = "asia-northeast1"
}

variable "subnet_cidr" {
  description = "CIDR for the es-subnet"
  type        = string
  default     = "10.146.0.0/24"
}

variable "es6_internal_ip" {
  description = "Reserved internal IP for the ES6 VM (whitelisted on ES9)"
  type        = string
  default     = "10.146.0.10"
}

variable "es9_internal_ip" {
  description = "Reserved internal IP for the ES9 VM"
  type        = string
  default     = "10.146.0.11"
}

variable "gke_pods_cidr" {
  description = "Secondary range for the rollback GKE cluster's pod IPs"
  type        = string
  default     = "10.148.0.0/18"
}

variable "gke_services_cidr" {
  description = "Secondary range for the rollback GKE cluster's service IPs"
  type        = string
  default     = "10.148.64.0/20"
}
