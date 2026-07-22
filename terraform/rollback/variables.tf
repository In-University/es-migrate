variable "project_id" {
  description = "GCP project ID"
  type        = string
  default     = "devhub-464904"
}

variable "region" {
  description = "GCP region (provider default; must match terraform/network's region)"
  type        = string
  default     = "asia-northeast1"
}

variable "zone" {
  description = "Zone for the rollback GKE Standard cluster (zonal, not regional -- see main.tf for why). Must be within var.region."
  type        = string
  default     = "asia-northeast1-a"
}

variable "gke_pods_cidr" {
  description = "Must match terraform/network's gke_pods_cidr — the GKE pod range allowed to reach ES on 9200."
  type        = string
  default     = "10.148.0.0/18"
}

variable "machine_type" {
  description = "Machine type for the single rollback node. e2-small (2 vCPU / 2GB) was tried first and OOMKilled the Logstash pod -- the chart's own default LS_JAVA_OPTS (-Xmx1g -Xms1g) plus its recommended 1536Mi container memory limit, plus the ~10 GKE system daemonsets sharing the node, don't fit in 2GB. e2-medium keeps the same 2 vCPU (no extra CPUS_ALL_REGIONS quota cost) but doubles memory to 4GB."
  type        = string
  default     = "e2-medium"
}
