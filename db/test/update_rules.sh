#!/bin/bash

# Shell script to create multiple rules using curl

# Define an array of rules
declare -a rules=(
  '{"type": "energy", "comparison_operator": ">", "threshold_value": 50, "rule_description": "High energy warning", "device_id": "e2e1a8d4-2e7a-4f0c-a35e-7b624f0a34e5", "severity": "WARNING", "consecutive_count": 3}'
  '{"type": "energy", "comparison_operator": "<", "threshold_value": 20, "rule_description": "Low energy warning", "device_id": "e2e1a8d4-2e7a-4f0c-a35e-7b624f0a34e5", "severity": "ERROR", "consecutive_count": 2}'
  '{"type": "energy", "comparison_operator": ">", "threshold_value": 55, "rule_description": "Critical High energy", "device_id": "e2e1a8d4-2e7a-4f0c-a35e-7b624f0a34e5", "severity": "FATAL", "consecutive_count": 4}'
  '{"type": "energy", "comparison_operator": "<", "threshold_value": 15, "rule_description": "Critical Low energy", "device_id": "e2e1a8d4-2e7a-4f0c-a35e-7b624f0a34e5", "severity": "ERROR", "consecutive_count": 5}'
)

# URL of the update_rule endpoint
url="http://192.168.49.2:30083/update_rule"

# Loop through each rule and send a PUT request
for i in "${!rules[@]}"; do
  rule_id=$((i + 1))
  rule="${rules[$i]}"
  echo "Updating rule: $rule"
  curl -X PUT "$url/$rule_id" -H "Content-Type: application/json" -d "$rule"
  echo -e "\n"
done

echo "All rules have been updated."
