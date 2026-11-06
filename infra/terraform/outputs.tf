output "data_bucket" {
  value = aws_s3_bucket.data.bucket
}

output "device_status_table" {
  value = aws_dynamodb_table.device_status.name
}

data "aws_iot_endpoint" "data" {
  endpoint_type = "iot:Data-ATS"
}

output "iot_endpoint" {
  value = data.aws_iot_endpoint.data.endpoint_address
}
