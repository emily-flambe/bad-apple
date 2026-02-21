terraform {
  backend "s3" {
    bucket                      = "bad-apple-tf-state"
    key                         = "terraform.tfstate"
    region                      = "auto"
    skip_credentials_validation = true
    skip_metadata_api_check     = true
    skip_region_validation      = true
    skip_requesting_account_id  = true
    skip_s3_checksum            = true
    use_path_style              = true
    endpoints = {
      s3 = "https://facf6619808dc039df729531bbb26d1d.r2.cloudflarestorage.com"
    }
  }
}
