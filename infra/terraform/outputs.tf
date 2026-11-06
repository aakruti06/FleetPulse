output "data_bucket" {
  value = aws_s3_bucket.data.bucket
}

output "device_status_table" {
  value = aws_dynamodb_table.device_status.name
}
