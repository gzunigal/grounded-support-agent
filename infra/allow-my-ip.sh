#!/usr/bin/env bash
# Re-run whenever your public IP changes: replaces the single port-8000 ingress rule.
set -euo pipefail
SG_ID=$(aws ec2 describe-security-groups --filters Name=group-name,Values=gsa-task --query 'SecurityGroups[0].GroupId' --output text)
MY_IP=$(curl -s https://checkip.amazonaws.com)/32
OLD=$(aws ec2 describe-security-groups --group-ids "$SG_ID" --query 'SecurityGroups[0].IpPermissions[?FromPort==`8000`].IpRanges[].CidrIp' --output text)
for cidr in $OLD; do
  aws ec2 revoke-security-group-ingress --group-id "$SG_ID" --protocol tcp --port 8000 --cidr "$cidr"
done
aws ec2 authorize-security-group-ingress --group-id "$SG_ID" --protocol tcp --port 8000 --cidr "$MY_IP" >/dev/null
echo "port 8000 open for $MY_IP"
