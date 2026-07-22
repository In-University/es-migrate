output "vpc_id" {
  value = google_compute_network.vpc.id
}

output "vpc_self_link" {
  value = google_compute_network.vpc.self_link
}

output "vpc_name" {
  value = google_compute_network.vpc.name
}

output "subnet_id" {
  value = google_compute_subnetwork.subnet.id
}

output "subnet_self_link" {
  value = google_compute_subnetwork.subnet.self_link
}

output "subnet_cidr" {
  value = google_compute_subnetwork.subnet.ip_cidr_range
}

output "es6_internal_ip" {
  value = google_compute_address.es6_internal.address
}

output "es9_internal_ip" {
  value = google_compute_address.es9_internal.address
}

output "gke_pods_range_name" {
  value = "gke-pods"
}

output "gke_services_range_name" {
  value = "gke-services"
}
