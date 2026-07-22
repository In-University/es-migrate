terraform {
  required_version = ">= 1.3.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ---------------------------------------------------------------------------
# Network layer — applied once, independently of the benchmark VM lifecycle.
#
# Owns the VPC, subnet, and the two reserved internal IPs. A GCP INTERNAL
# reserved address holds a reference to the subnet it was reserved in, so the
# subnet has to live in this same state — otherwise destroying the subnet
# from the main benchmark state would be blocked by GCP while these
# reservations still reference it. `terraform destroy` is never run here;
# only `terraform/` (the benchmark VMs) gets destroyed per cycle.
# ---------------------------------------------------------------------------

resource "google_compute_network" "vpc" {
  name                    = "es-migrate-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "subnet" {
  name          = "es-subnet"
  ip_cidr_range = var.subnet_cidr
  region        = var.region
  network       = google_compute_network.vpc.id

  # Secondary ranges consumed by the rollback GKE cluster
  # (terraform/rollback/), which is VPC-native and needs pod/service ranges
  # on this subnet. Declared here rather than left to GKE auto-allocation so
  # the ranges are visible and stable independent of whether rollback/ has
  # ever been applied.
  secondary_ip_range {
    range_name    = "gke-pods"
    ip_cidr_range = var.gke_pods_cidr
  }
  secondary_ip_range {
    range_name    = "gke-services"
    ip_cidr_range = var.gke_services_cidr
  }
}

resource "google_compute_address" "es6_internal" {
  name         = "es6-internal-ip"
  subnetwork   = google_compute_subnetwork.subnet.id
  address_type = "INTERNAL"
  address      = var.es6_internal_ip
  region       = var.region
}

resource "google_compute_address" "es9_internal" {
  name         = "es9-internal-ip"
  subnetwork   = google_compute_subnetwork.subnet.id
  address_type = "INTERNAL"
  address      = var.es9_internal_ip
  region       = var.region
}
