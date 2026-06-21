terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.12"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# ----------------------------------------------------------
# Dynamic auth for Helm provider
# ----------------------------------------------------------
data "google_client_config" "default" {}

provider "helm" {
  kubernetes {
    host                   = "https://${google_container_cluster.primary.endpoint}"
    token                  = data.google_client_config.default.access_token
    cluster_ca_certificate = base64decode(google_container_cluster.primary.master_auth[0].cluster_ca_certificate)
  }
}

# ----------------------------------------------------------
# GKE Cluster
# ----------------------------------------------------------
resource "google_container_cluster" "primary" {
  name     = var.cluster_name
  location = var.zone

  remove_default_node_pool = true
  initial_node_count       = 1

  # Habilitar Workload Identity para no usar static keys
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }
}

# Node Pool: Infraestructura (RabbitMQ, Redis)
resource "google_container_node_pool" "infra_pool" {
  name       = "infra-pool"
  cluster    = google_container_cluster.primary.id
  node_count = 2

  node_config {
    preemptible  = true
    machine_type = "e2-medium"
    
    labels = {
      node_role = "infrastructure"
    }

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
  }
}

# Node Pool: Aplicaciones (Frontend, NCT, TrP, CPU Workers)
resource "google_container_node_pool" "apps_pool" {
  name       = "apps-pool"
  cluster    = google_container_cluster.primary.id
  
  autoscaling {
    min_node_count = 2
    max_node_count = 10
  }

  node_config {
    preemptible  = true
    machine_type = "e2-standard-4"

    labels = {
      node_role = "applications"
    }

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
  }
}

# ----------------------------------------------------------
# Static IP for Nginx Ingress
# ----------------------------------------------------------
resource "google_compute_address" "nginx_ingress_ip" {
  name   = "nginx-ingress-ip"
  region = var.region
}

# ----------------------------------------------------------
# ingress-nginx via Helm
# ----------------------------------------------------------
resource "helm_release" "ingress_nginx" {
  name             = "ingress-nginx"
  repository       = "https://kubernetes.github.io/ingress-nginx"
  chart            = "ingress-nginx"
  version          = "4.12.1"
  namespace        = "ingress-nginx"
  create_namespace = true
  wait             = true
  timeout          = 600

  set {
    name  = "controller.service.loadBalancerIP"
    value = google_compute_address.nginx_ingress_ip.address
  }

  set {
    name  = "controller.service.externalTrafficPolicy"
    value = "Local"
  }

  depends_on = [google_container_node_pool.infra_pool, google_container_node_pool.apps_pool]
}

# ----------------------------------------------------------
# cert-manager via Helm (para certificados HTTPS)
# ----------------------------------------------------------
resource "helm_release" "cert_manager" {
  name             = "cert-manager"
  repository       = "https://charts.jetstack.io"
  chart            = "cert-manager"
  version          = "1.17.2"
  namespace        = "cert-manager"
  create_namespace = true
  wait             = true
  timeout          = 600

  set {
    name  = "crds.enabled"
    value = "true"
  }

  depends_on = [google_container_node_pool.infra_pool, google_container_node_pool.apps_pool]
}
