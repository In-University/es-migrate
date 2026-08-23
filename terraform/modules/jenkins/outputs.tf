output "jenkins_instance_name" {
  description = "Name of the Jenkins instance"
  value       = google_compute_instance.jenkins.name
}

output "jenkins_internal_ip" {
  description = "The reserved static internal IP address assigned to Jenkins"
  value       = google_compute_instance.jenkins.network_interface[0].network_ip
}

output "jenkins_external_ip" {
  description = "The public IP address assigned to Jenkins VM"
  value       = google_compute_instance.jenkins.network_interface[0].access_config[0].nat_ip
}

output "jenkins_url_internal" {
  description = "Internal URL to access Jenkins UI"
  value       = "http://${google_compute_instance.jenkins.network_interface[0].network_ip}:8080"
}

output "jenkins_url_external" {
  description = "External URL to access Jenkins UI"
  value       = "http://${google_compute_instance.jenkins.network_interface[0].access_config[0].nat_ip}:8080"
}
