output "cluster_name" {
  value = google_container_cluster.rollback.name
}

output "cluster_endpoint" {
  value     = google_container_cluster.rollback.endpoint
  sensitive = true
}

output "get_credentials" {
  value = "gcloud container clusters get-credentials ${google_container_cluster.rollback.name} --zone=${var.zone} --project=${var.project_id}"
}
