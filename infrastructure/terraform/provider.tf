provider "google" {
  project = var.project_id
  region  = var.region
}

provider "kubernetes" {
  host  = "https://127.0.0.1"
  token = "dummy"
  insecure = true
}

data "google_client_config" "default" {}
