variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "asia-northeast1"
}

variable "zone" {
  description = "GCP Zone"
  type        = string
  default     = "asia-northeast1-a"
}

variable "network_id" {
  description = "VPC Network ID or name"
  type        = string
}

variable "subnet_id" {
  description = "Subnetwork ID or name"
  type        = string
}

variable "instance_name" {
  description = "Name of the Jenkins VM instance"
  type        = string
  default     = "jenkins-server"
}

variable "machine_type" {
  description = "Machine type for the Jenkins VM (e2-small or e2-medium recommended)"
  type        = string
  default     = "e2-medium"
}

variable "boot_disk_gb" {
  description = "Boot disk size in GB"
  type        = number
  default     = 20
}

variable "boot_image" {
  description = "OS Image for the VM"
  type        = string
  default     = "ubuntu-os-cloud/ubuntu-2204-lts"
}

variable "jenkins_internal_ip" {
  description = "Reserved static internal IP address for the Jenkins VM (from network module remote state output)"
  type        = string
}

variable "jenkins_version" {
  description = "Jenkins Docker container image tag"
  type        = string
  default     = "2.504.3"
}

variable "jenkins_admin_user" {
  description = "Initial Admin Username for Jenkins"
  type        = string
  default     = "admin"
}

variable "jenkins_admin_password" {
  description = "Initial Admin Password for Jenkins"
  type        = string
  default     = "admin123"
  sensitive   = true
}

variable "allowed_ingress_cidrs" {
  description = "CIDR blocks allowed to access Jenkins web UI (port 8080)"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}
