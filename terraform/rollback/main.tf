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
# Ephemeral rollback infrastructure — applied only when a blue-green rollback
# is in flight, destroyed right after. Not part of the normal benchmark
# apply/destroy cycle (terraform/) and never touches terraform/network/.
# ---------------------------------------------------------------------------
data "terraform_remote_state" "network" {
  backend = "local"
  config = {
    path = "${path.module}/../network/terraform.tfstate"
  }
}

# GKE Standard with a single, manually-sized small node -- not Autopilot.
# Autopilot mandates a *regional* cluster (GCP rejects zonal Autopilot
# outright: "Autopilot clusters must be regional clusters"), and a regional
# cluster reserves system-workload capacity across 3 zones for HA, which
# alone needs ~8 vCPU of CPUS_ALL_REGIONS quota. The 2 benchmark VMs
# (e2-standard-4 x2 = 8 vCPU) already consume most of a default 12-vCPU
# project quota, so Autopilot here reliably fails with
# INSUFFICIENT_QUOTA_PROJECT while the ES VMs are up -- which they must be,
# since Logstash needs both reachable during the sync. Standard mode lets
# the node pool below be pinned to a single smallest-practical machine type
# (e2-small, 2 vCPU) instead, which fits the remaining quota headroom; the
# tradeoff is we now own node sizing/lifecycle instead of Autopilot doing it.
resource "google_container_cluster" "rollback" {
  name     = "es-rollback"
  location = var.zone

  remove_default_node_pool = true
  initial_node_count       = 0
  deletion_protection      = false

  network    = data.terraform_remote_state.network.outputs.vpc_self_link
  subnetwork = data.terraform_remote_state.network.outputs.subnet_self_link

  ip_allocation_policy {
    cluster_secondary_range_name  = data.terraform_remote_state.network.outputs.gke_pods_range_name
    services_secondary_range_name = data.terraform_remote_state.network.outputs.gke_services_range_name
  }

  timeouts {
    create = "30m"
    update = "30m"
    delete = "30m"
  }
}

resource "google_container_node_pool" "rollback_nodes" {
  name       = "rollback-pool"
  cluster    = google_container_cluster.rollback.id
  location   = var.zone
  node_count = 1

  node_config {
    machine_type = var.machine_type
    disk_size_gb = 30
    oauth_scopes = [
      "https://www.googleapis.com/auth/devstorage.read_only",
      "https://www.googleapis.com/auth/logging.write",
      "https://www.googleapis.com/auth/monitoring",
    ]
  }

  timeouts {
    create = "20m"
    update = "20m"
    delete = "20m"
  }
}

# Scoped to the pod range only (not the whole subnet like es-allow-internal)
# and owned by this ephemeral state, so it exists exactly as long as the
# rollback cluster does — no need to touch the main root's firewall config
# to grant it, and nothing lingers after `terraform destroy` here.
resource "google_compute_firewall" "rollback_to_es" {
  name    = "es-allow-rollback-gke"
  network = data.terraform_remote_state.network.outputs.vpc_id

  allow {
    protocol = "tcp"
    ports    = ["9200"]
  }

  source_ranges = [var.gke_pods_cidr]
  target_tags   = ["es-node"]
}
