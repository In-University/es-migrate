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
# Network — owned by terraform/network/ (separate state, applied once and
# never destroyed as part of this root). Reserved internal addresses can't
# live here: they'd be destroyed along with everything else in this root on
# `terraform destroy`, and the ES9 startup script needs a stable ES6 address
# across benchmark cycles.
# ---------------------------------------------------------------------------
data "terraform_remote_state" "network" {
  backend = "local"
  config = {
    path = "${path.module}/network/terraform.tfstate"
  }
}

# ---------------------------------------------------------------------------
# Firewall
# ---------------------------------------------------------------------------

# ES9 -> ES6 remote reindex (9200) + transport (9300) + icmp, within the subnet.
resource "google_compute_firewall" "internal" {
  name    = "es-allow-internal"
  network = data.terraform_remote_state.network.outputs.vpc_id

  allow {
    protocol = "tcp"
    ports    = ["9200", "9300"]
  }
  allow {
    protocol = "icmp"
  }

  source_ranges = [data.terraform_remote_state.network.outputs.subnet_cidr]
  target_tags   = ["es-node"]
}

# SSH from your IP.
resource "google_compute_firewall" "ssh" {
  name    = "es-allow-ssh"
  network = data.terraform_remote_state.network.outputs.vpc_id

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = [var.your_ip]
  target_tags   = ["es-node"]
}

# Optional: reach ES HTTP (9200) from your IP to curl/inspect and trigger the reindex.
resource "google_compute_firewall" "es_admin" {
  count   = var.enable_es_admin_ingress ? 1 : 0
  name    = "es-allow-es-admin"
  network = data.terraform_remote_state.network.outputs.vpc_id

  allow {
    protocol = "tcp"
    ports    = ["9200"]
  }

  source_ranges = [var.your_ip]
  target_tags   = ["es-node"]
}

# ---------------------------------------------------------------------------
# VMs
# ---------------------------------------------------------------------------
resource "google_compute_instance" "es6" {
  name         = "es6-source"
  machine_type = var.machine_type
  zone         = var.zone_es6
  tags         = ["es-node"]

  boot_disk {
    initialize_params {
      image = var.boot_image
      size  = var.boot_disk_gb
      type  = "pd-ssd"
    }
  }

  network_interface {
    subnetwork = data.terraform_remote_state.network.outputs.subnet_id
    network_ip = data.terraform_remote_state.network.outputs.es6_internal_ip
    access_config {} # ephemeral external IP
  }

  metadata_startup_script = templatefile("${path.module}/startup-es6.sh.tpl", {
    es6_image        = var.es6_image
    es_heap          = var.es_heap
    elastic_password = var.elastic_password
  })
}

resource "google_compute_instance" "es9" {
  name         = "es9-dest"
  machine_type = var.machine_type
  zone         = var.zone_es9
  tags         = ["es-node"]

  boot_disk {
    initialize_params {
      image = var.boot_image
      size  = var.boot_disk_gb
      type  = "pd-ssd"
    }
  }

  network_interface {
    subnetwork = data.terraform_remote_state.network.outputs.subnet_id
    network_ip = data.terraform_remote_state.network.outputs.es9_internal_ip
    access_config {} # ephemeral external IP
  }

  metadata_startup_script = templatefile("${path.module}/startup-es9.sh.tpl", {
    es9_image        = var.es9_image
    es_heap          = var.es_heap
    es6_internal_ip  = data.terraform_remote_state.network.outputs.es6_internal_ip
    elastic_password = var.elastic_password
  })
}
