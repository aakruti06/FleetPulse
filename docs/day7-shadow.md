# Day 7: Device shadow (remote configuration)

The simulator subscribes to its shadow delta topic and changes its publish interval when the cloud sets a new desired value.

## Flow
1. Cloud sets desired interval_sec in the classic shadow
2. AWS publishes the delta to $aws/things/<device>/shadow/update/delta
3. Device validates (1 to 60 seconds), applies it, and reports the new value
4. Reported matches desired, so the delta clears

## Policy
fleetpulse-fleet-policy now allows each device to publish, subscribe to and receive only its own shadow topics, using the thing-name policy variable.

## Result
Changing desired interval_sec from 2 to 10 in the console slowed the device's publishing to match. A desired value set before the device started was applied on connect.

## Problem solved
Shadow setup timed out because the updated policy version was saved but not set as active. Setting it active fixed it.

## Limitations
- Only one setting (interval_sec) is managed
- The endpoint is hardcoded in simulator.py (move it to an environment variable)
- No automated tests yet
