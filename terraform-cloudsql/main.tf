terraform {
  required_version = ">= 1.3.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "random_id" "suffix" {
  byte_length = 4
}

# ---------------------------------------------------------------------------
# 1. Primary Instance (PostgreSQL)
# ---------------------------------------------------------------------------
resource "google_sql_database_instance" "primary" {
  name             = "pg-master-${random_id.suffix.hex}"
  database_version = var.db_version
  region           = var.region

  deletion_protection = false

  settings {
    tier              = var.tier
    disk_size         = 10
    disk_type         = "PD_SSD"
    availability_type = "ZONAL"

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = false
    }

    ip_configuration {
      ipv4_enabled = true
    }
  }
}

# ---------------------------------------------------------------------------
# Default User: postgres with password "postgres"
# ---------------------------------------------------------------------------
resource "google_sql_user" "default_user" {
  name     = "postgres"
  instance = google_sql_database_instance.primary.name
  password = "postgres"
}

# ---------------------------------------------------------------------------
# 2. Read Replica 1
# ---------------------------------------------------------------------------
resource "google_sql_database_instance" "replica_1" {
  name                 = "pg-replica-1-${random_id.suffix.hex}"
  master_instance_name = google_sql_database_instance.primary.name
  database_version     = var.db_version
  region               = var.region

  deletion_protection = false

  settings {
    tier              = var.tier
    disk_size         = 10
    disk_type         = "PD_SSD"
    availability_type = "ZONAL"

    ip_configuration {
      ipv4_enabled = true
    }
  }

  depends_on = [google_sql_database_instance.primary]
}

# ---------------------------------------------------------------------------
# 3. Read Replica 2
# ---------------------------------------------------------------------------
resource "google_sql_database_instance" "replica_2" {
  name                 = "pg-replica-2-${random_id.suffix.hex}"
  master_instance_name = google_sql_database_instance.primary.name
  database_version     = var.db_version
  region               = var.region

  deletion_protection = false

  settings {
    tier              = var.tier
    disk_size         = 10
    disk_type         = "PD_SSD"
    availability_type = "ZONAL"

    ip_configuration {
      ipv4_enabled = true
    }
  }

  depends_on = [google_sql_database_instance.primary]
}
