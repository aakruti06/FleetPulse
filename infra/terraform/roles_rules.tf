locals {
  rule_prefix = replace(var.name_prefix, "-", "_")
}

data "aws_iam_policy_document" "iot_assume" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["iot.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [local.account]
    }
  }
}

resource "aws_iam_role" "rule_s3" {
  name               = "${var.name_prefix}-iot-s3-role"
  assume_role_policy = data.aws_iam_policy_document.iot_assume.json
}

resource "aws_iam_role_policy" "rule_s3" {
  name = "write-raw-data"
  role = aws_iam_role.rule_s3.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "s3:PutObject"
      Resource = "${aws_s3_bucket.data.arn}/raw/*"
    }]
  })
}

resource "aws_iam_role" "rule_dynamodb" {
  name               = "${var.name_prefix}-iot-dynamodb-role"
  assume_role_policy = data.aws_iam_policy_document.iot_assume.json
}

resource "aws_iam_role_policy" "rule_dynamodb" {
  name = "write-device-status"
  role = aws_iam_role.rule_dynamodb.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "dynamodb:PutItem"
      Resource = aws_dynamodb_table.device_status.arn
    }]
  })
}

resource "aws_iot_topic_rule" "to_s3" {
  name        = "${local.rule_prefix}_to_s3"
  enabled     = true
  sql         = "SELECT * FROM '${var.topic_prefix}/+/telemetry'"
  sql_version = "2016-03-23"

  s3 {
    bucket_name = aws_s3_bucket.data.bucket
    key         = "raw/$${parse_time(\"yyyy-MM-dd\", timestamp())}/$${topic(2)}/$${timestamp()}.json"
    role_arn    = aws_iam_role.rule_s3.arn
  }
}

resource "aws_iot_topic_rule" "to_dynamodb" {
  name        = "${local.rule_prefix}_to_dynamodb"
  enabled     = true
  sql         = "SELECT *, timestamp() AS received_at FROM '${var.topic_prefix}/+/telemetry'"
  sql_version = "2016-03-23"

  dynamodbv2 {
    role_arn = aws_iam_role.rule_dynamodb.arn

    put_item {
      table_name = aws_dynamodb_table.device_status.name
    }
  }
}
