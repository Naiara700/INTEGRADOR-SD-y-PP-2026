variable "project_id" {
  description = "The ID of the GCP project"
  type        = string
  default     = "project-f3583ede-db03-4872-95c"  
}

variable "region" {
  description = "The GCP region"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "The GCP zone"
  type        = string
  default     = "us-central1-a"
}

variable "cluster_name" {
  description = "The name of the GKE cluster"
  type        = string
  default     = "stickerchain-cluster"
}

variable "domain" {
  description = "Domain name for TLS and Ingress"
  type        = string
  default     = "stickerchain.lat"
}

variable "letsencrypt_email" {
  description = "Email for Let's Encrypt certificate notifications"
  type        = string
  default     = "abril.nadia.babino984@gmail.com"
}
