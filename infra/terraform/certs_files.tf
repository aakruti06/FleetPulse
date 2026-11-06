data "http" "amazon_root_ca" {
  url = "https://www.amazontrust.com/repository/AmazonRootCA1.pem"

  lifecycle {
    postcondition {
      condition     = self.status_code == 200
      error_message = "Could not download the Amazon root certificate."
    }
  }
}

locals {
  certs_dir = "${path.module}/../../certs"
}

resource "local_sensitive_file" "certificate" {
  for_each        = aws_iot_certificate.device
  filename        = "${local.certs_dir}/${var.name_prefix}-device-${each.key}/${var.name_prefix}-device-${each.key}-certificate.pem.crt"
  content         = each.value.certificate_pem
  file_permission = "0600"
}

resource "local_sensitive_file" "private_key" {
  for_each        = aws_iot_certificate.device
  filename        = "${local.certs_dir}/${var.name_prefix}-device-${each.key}/${var.name_prefix}-device-${each.key}-private.pem.key"
  content         = each.value.private_key
  file_permission = "0600"
}

resource "local_file" "root_ca" {
  for_each = aws_iot_thing.device
  filename = "${local.certs_dir}/${each.value.name}/AmazonRootCA1.pem"
  content  = data.http.amazon_root_ca.response_body
}
