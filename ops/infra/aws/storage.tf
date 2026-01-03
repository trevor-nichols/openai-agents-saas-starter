resource "aws_s3_bucket" "storage" {
  count  = var.create_s3_bucket ? 1 : 0
  bucket = var.storage_bucket_name
}

resource "aws_s3_bucket_public_access_block" "storage" {
  count  = var.create_s3_bucket && var.s3_block_public_access ? 1 : 0
  bucket = aws_s3_bucket.storage[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "storage" {
  count  = var.create_s3_bucket && var.s3_enable_encryption ? 1 : 0
  bucket = aws_s3_bucket.storage[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = var.s3_kms_key_id != "" ? "aws:kms" : "AES256"
      kms_master_key_id = var.s3_kms_key_id != "" ? var.s3_kms_key_id : null
    }
  }
}

resource "aws_s3_bucket_versioning" "storage" {
  count  = var.create_s3_bucket ? 1 : 0
  bucket = aws_s3_bucket.storage[0].id

  versioning_configuration {
    status = var.s3_enable_versioning ? "Enabled" : "Suspended"
  }
}
