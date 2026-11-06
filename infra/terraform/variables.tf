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

variable "device_ids" {
  description = "Suffixes for the device names (prefix-device-<id>)"
  type        = set(string)
  default     = ["001", "002", "003"]
}

variable "topic_prefix" {
  description = "MQTT topic prefix for this stack, separate from the hand-built stack"
  type        = string
  default     = "fleetpulse-tf"
}
