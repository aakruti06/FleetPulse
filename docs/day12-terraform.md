# Day 12: Terraform basics

Terraform builds a second copy of the stack (prefix fleetpulse-tf), separate from the hand-built one, so the working demo stays untouched and the rebuild can be proven later.

## What exists so far
- S3 data bucket (public access blocked, force_destroy for demo data)
- DynamoDB device-status table (key device_id, on-demand billing)
- Default tags: Project and ManagedBy on every resource

## State
Remote state in a private, versioned S3 bucket with encryption and S3-native locking (Terraform 1.10 or later). The state bucket is created by hand once, because Terraform cannot create the bucket that holds its own state.

## How to run
    source ~/.fleetpulse-tf.env    # credentials, kept outside the repo
    cd infra/terraform
    terraform init
    terraform plan
    terraform apply

## Result
First apply created 3 resources. A second plan reported No changes, so the code matches reality.

## Security notes
- Credentials live in a file outside the repo with restricted permissions
- The state file is never committed (see .gitignore)
- The Terraform user has broad permissions for learning (to be replaced by short-lived credentials and narrower permissions in a real setup)

## Next
IoT policy, things and certificates, IoT rules, IAM roles, Lambdas and the API.
