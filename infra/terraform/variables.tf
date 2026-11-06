variable "region" {
  type    = string
  default = "ap-south-1"
}

variable "name_prefix" {
  description = "Prefix for every resource name in this stack"
  type        = string
  default     = "fleetpulse-tf"
}

variable "bucket_suffix" {
  description = "Makes the S3 bucket name globally unique"
  type        = string
  default     = "fp-26"
}
