resource "aws_s3_bucket" "data" {
  bucket        = "${var.name_prefix}-raw-${var.bucket_suffix}"
  force_destroy = true # demo data only, so destroy can delete a non-empty bucket
}

resource "aws_s3_bucket_public_access_block" "data" {
  bucket                  = aws_s3_bucket.data.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_dynamodb_table" "device_status" {
  name         = "${var.name_prefix}-device-status"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "device_id"

  attribute {
    name = "device_id"
    type = "S"
  }
}
