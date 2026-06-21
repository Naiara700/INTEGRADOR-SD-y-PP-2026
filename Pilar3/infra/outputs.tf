output "kubernetes_cluster_name" {
  value       = google_container_cluster.primary.name
  description = "GKE Cluster Name"
}

output "kubernetes_cluster_host" {
  value       = google_container_cluster.primary.endpoint
  description = "GKE Cluster Host"
}

output "nginx_ingress_ip" {
  value       = google_compute_address.nginx_ingress_ip.address
  description = "Static IP assigned to nginx ingress controller LoadBalancer"
}
