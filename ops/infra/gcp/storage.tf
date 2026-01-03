resource "google_storage_bucket" "main" {
  name                        = var.storage_bucket_name
  location                    = local.storage_location
  uniform_bucket_level_access = var.storage_uniform_access
  force_destroy               = var.storage_force_destroy
  public_access_prevention    = "enforced"

  versioning {
    enabled = var.storage_versioning_enabled
  }
}

resource "google_storage_bucket_iam_member" "runtime" {
  bucket = google_storage_bucket.main.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.runtime.email}"
}
