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

resource "cloudflare_r2_bucket" "video" {
  account_id = var.cloudflare_account_id
  name       = "bad-apple-video"
}

resource "cloudflare_workers_script" "bad_apple" {
  account_id     = var.cloudflare_account_id
  script_name    = "bad-apple"
  content_file   = "${path.module}/worker/index.js"
  content_sha256 = filesha256("${path.module}/worker/index.js")
  main_module    = "index.js"

  assets = {
    directory = "${path.module}/../public"
  }

  bindings = [{
    type        = "r2_bucket"
    name        = "VIDEO_BUCKET"
    bucket_name = cloudflare_r2_bucket.video.name
  }]
}

resource "cloudflare_workers_script_subdomain" "bad_apple" {
  account_id  = var.cloudflare_account_id
  script_name = cloudflare_workers_script.bad_apple.script_name
  enabled     = true
}

resource "cloudflare_workers_custom_domain" "bad_apple" {
  account_id = var.cloudflare_account_id
  hostname   = "bad-apple.emilycogsdill.com"
  service    = cloudflare_workers_script.bad_apple.script_name
  zone_id    = var.cloudflare_zone_id
}
