# Day 10: OTA updates with AWS IoT Jobs

Flow: update package + checksum in S3 -> job document with a presigned URL placeholder -> device asks for its next job -> device downloads over HTTPS -> verifies SHA-256 -> applies -> reports to the job and the shadow

## Pieces
- ota/fleetpulse-1.1.0.json: the update package (sets the default publish interval to 5 seconds)
- ota/job-1.1.0.json: the job document (operation, version, URL placeholder, sha256)
- device/ota.py: checksum verification, package validation and HTTPS download
- device/simulator.py: subscribes to notify-next, asks for jobs on start and reconnect, reports status
- Role fleetpulse-iot-jobs-role: read-only access to the updates/ prefix, trusted only by IoT in my own account (aws:SourceAccount)
- Fleet policy: per-device permissions for the jobs topics

## Result
Job ota-1-1-0-device-001 succeeded on device 001. The device downloaded the package through a temporary link, verified the checksum, applied the new interval and reported firmware 1.1.0 in its shadow.

## Problem solved
The shadow still held the old desired interval, which would have reverted the update. The update now sets the desired value as well.

## Limitations
- The firmware version is not saved across restarts
- Packages are checksummed but not signed
- No automatic rollback
- Only one device targeted so far (fleet rollout is next)
