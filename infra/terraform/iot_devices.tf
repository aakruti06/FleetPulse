data "aws_caller_identity" "current" {}

locals {
  account = data.aws_caller_identity.current.account_id
  iot_arn = "arn:aws:iot:${var.region}:${local.account}"
  # $$ escapes Terraform's own interpolation, so IoT sees ${iot:Connection.Thing.ThingName}
  thing = "$${iot:Connection.Thing.ThingName}"
}

resource "aws_iot_thing" "device" {
  for_each = var.device_ids
  name     = "${var.name_prefix}-device-${each.key}"
}

resource "aws_iot_certificate" "device" {
  for_each = aws_iot_thing.device
  active   = true
}

resource "aws_iot_thing_principal_attachment" "device" {
  for_each  = aws_iot_thing.device
  thing     = each.value.name
  principal = aws_iot_certificate.device[each.key].arn
}

resource "aws_iot_policy" "fleet" {
  name = "${var.name_prefix}-fleet-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "iot:Connect"
        Resource = "${local.iot_arn}:client/${local.thing}"
      },
      {
        Effect = "Allow"
        Action = "iot:Publish"
        Resource = [
          "${local.iot_arn}:topic/${var.topic_prefix}/${local.thing}/telemetry",
          "${local.iot_arn}:topic/$aws/things/${local.thing}/shadow/*",
          "${local.iot_arn}:topic/$aws/things/${local.thing}/jobs/*",
        ]
      },
      {
        Effect = "Allow"
        Action = "iot:Subscribe"
        Resource = [
          "${local.iot_arn}:topicfilter/$aws/things/${local.thing}/shadow/*",
          "${local.iot_arn}:topicfilter/$aws/things/${local.thing}/jobs/*",
        ]
      },
      {
        Effect = "Allow"
        Action = "iot:Receive"
        Resource = [
          "${local.iot_arn}:topic/$aws/things/${local.thing}/shadow/*",
          "${local.iot_arn}:topic/$aws/things/${local.thing}/jobs/*",
        ]
      },
    ]
  })
}

resource "aws_iot_policy_attachment" "device" {
  for_each = aws_iot_certificate.device
  policy   = aws_iot_policy.fleet.name
  target   = each.value.arn
}
