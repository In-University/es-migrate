output "primary_name" {
  value = google_sql_database_instance.primary.name
}

output "primary_ip" {
  value = google_sql_database_instance.primary.public_ip_address
}

output "primary_database_version" {
  value = google_sql_database_instance.primary.database_version
}

output "replica_1_name" {
  value = google_sql_database_instance.replica_1.name
}

output "replica_1_ip" {
  value = google_sql_database_instance.replica_1.public_ip_address
}

output "replica_2_name" {
  value = google_sql_database_instance.replica_2.name
}

output "replica_2_ip" {
  value = google_sql_database_instance.replica_2.public_ip_address
}
