variable "project_id" {
  description = "GCP project ID"
  type        = string
  default     = "devhub-464904"
}

variable "region" {
  description = "GCP region for the VPC subnet and both VMs"
  type        = string
  default     = "asia-northeast1"
}

variable "zone_es6" {
  description = "Zone for the Elasticsearch 6 (source) VM"
  type        = string
  default     = "asia-northeast1-a"
}

variable "zone_es9" {
  description = "Zone for the Elasticsearch 9 (destination) VM"
  type        = string
  default     = "asia-northeast1-b"
}

variable "machine_type" {
  description = "Machine type for both ES VMs (4 vCPU / 16 GB)"
  type        = string
  default     = "e2-standard-4"
}

variable "boot_disk_gb" {
  description = "Boot disk size in GB (holds OS + Docker + ES data)"
  type        = number
  default     = 30
}

variable "boot_image" {
  description = "Boot image (Ubuntu 22.04 LTS)"
  type        = string
  default     = "ubuntu-os-cloud/ubuntu-2204-lts"
}

variable "es6_image" {
  description = "Elasticsearch 6 Docker image (source cluster)"
  type        = string
  default     = "docker.elastic.co/elasticsearch/elasticsearch:6.8.23"
}

variable "es9_image" {
  description = "Elasticsearch 9 Docker image (destination cluster). Verify latest 9.x patch before apply."
  type        = string
  default     = "docker.elastic.co/elasticsearch/elasticsearch:9.0.4"
}

variable "es_heap" {
  description = "JVM heap for each ES node (keep <= 50% of RAM)"
  type        = string
  default     = "8g"
}

variable "elastic_password" {
  description = "Password for the built-in 'elastic' superuser on both nodes (seeded at first boot). Defaults to 'elastic' (7 chars, meets the ES 6-char minimum)."
  type        = string
  default     = "elastic"
  sensitive   = true
}

variable "your_ip" {
  description = "CIDR allowed to reach SSH (22) and the ES HTTP admin port (9200). Set to your.public.ip/32. Default 0.0.0.0/0 is OPEN TO THE INTERNET - restrict this."
  type        = string
  default     = "0.0.0.0/0"
}

variable "enable_es_admin_ingress" {
  description = "If true, allow tcp 9200 from var.your_ip (curl/inspect + run reindex from laptop)."
  type        = bool
  default     = true
}
