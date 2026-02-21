terraform {
  required_version = ">= 1.0"
  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "= 5.17.0"
    }
  }
}

provider "cloudflare" {}

resource "cloudflare_workers_script" "bad_apple" {
  account_id     = var.cloudflare_account_id
  script_name    = "bad-apple"
  content_file   = "${path.module}/worker/index.js"
  content_sha256 = filesha256("${path.module}/worker/index.js")
  main_module    = "index.js"

  assets = {
    directory = "${path.module}/../public"
  }
}

resource "cloudflare_workers_script_subdomain" "bad_apple" {
  account_id = var.cloudflare_account_id
  script_name = cloudflare_workers_script.bad_apple.script_name
  enabled    = true
}
