output "es6_internal_ip" {
  value = data.terraform_remote_state.network.outputs.es6_internal_ip
}

output "es6_external_ip" {
  value = google_compute_instance.es6.network_interface[0].access_config[0].nat_ip
}

output "es9_internal_ip" {
  value = data.terraform_remote_state.network.outputs.es9_internal_ip
}

output "es9_external_ip" {
  value = google_compute_instance.es9.network_interface[0].access_config[0].nat_ip
}

output "ssh_es6" {
  value = "gcloud compute ssh es6-source --zone=${var.zone_es6} --project=${var.project_id}"
}

output "ssh_es9" {
  value = "gcloud compute ssh es9-dest --zone=${var.zone_es9} --project=${var.project_id}"
}

output "elastic_user" {
  value = "elastic"
}

# Both nodes come up secured with the same elastic password (var.elastic_password).
# These embed the password, so they are marked sensitive; view with:
#   terraform output -raw check_es6
output "check_es6" {
  value     = "curl -u elastic:${var.elastic_password} http://${google_compute_instance.es6.network_interface[0].access_config[0].nat_ip}:9200/_security/_authenticate"
  sensitive = true
}

output "check_es9" {
  value     = "curl -u elastic:${var.elastic_password} http://${google_compute_instance.es9.network_interface[0].access_config[0].nat_ip}:9200/_security/_authenticate"
  sensitive = true
}
