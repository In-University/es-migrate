terraform {
  required_version = ">= 1.3.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.0.0, < 6.0.0"
    }
  }
}

# ---------------------------------------------------------------------------
# 1. Firewall Rule for Jenkins UI (Port 8080) & Agent JNLP (Port 50000)
# ---------------------------------------------------------------------------
resource "google_compute_firewall" "jenkins_ingress" {
  name    = "${var.instance_name}-allow-ingress"
  network = var.network_id

  allow {
    protocol = "tcp"
    ports    = ["22", "8080", "50000"]
  }

  source_ranges = var.allowed_ingress_cidrs
  target_tags   = ["jenkins-server"]
}

# ---------------------------------------------------------------------------
# 2. Compute Engine Instance for Jenkins 2.504
# ---------------------------------------------------------------------------
resource "google_compute_instance" "jenkins" {
  name         = var.instance_name
  machine_type = var.machine_type
  zone         = var.zone
  tags         = ["jenkins-server"]

  boot_disk {
    initialize_params {
      image = var.boot_image
      size  = var.boot_disk_gb
      type  = "pd-standard"
    }
  }

  network_interface {
    subnetwork = var.subnet_id
    network_ip = var.jenkins_internal_ip

    # Public IP required for downloading Docker and pulling jenkins/jenkins image from Docker Hub
    access_config {}
  }

  metadata_startup_script = replace(templatefile("${path.module}/templates/startup.sh.tpl", {
    jenkins_version = var.jenkins_version
    init_groovy_script = templatefile("${path.module}/templates/init_jenkins.groovy.tpl", {
      jenkins_admin_user     = var.jenkins_admin_user
      jenkins_admin_password = var.jenkins_admin_password
    })
  }), "\r\n", "\n")
}
