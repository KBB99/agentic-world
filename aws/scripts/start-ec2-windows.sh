#!/usr/bin/env bash
# Start the Windows GPU EC2 instance and print connection details
# Inspired by aws/scripts/start-medialive-channel.sh
# Usage examples:
#   bash aws/scripts/start-ec2-windows.sh
#   REGION=us-east-1 bash aws/scripts/start-ec2-windows.sh --instance-id i-0123456789abcdef0
#   bash aws/scripts/start-ec2-windows.sh --region us-east-1 --name agentic-demo-gpu
#   bash aws/scripts/start-ec2-windows.sh --no-wait   # do not wait for running

set -euo pipefail

# --- Helpers ---
err() { echo "ERROR: $*" 1>&2; }
need() { command -v "$1" >/dev/null || { err "Missing dependency: $1"; exit 1; } }
usage() {
  cat 1>&2 <<USAGE
Start the Windows GPU EC2 instance used for Unreal/OBS and print Public IP/DNS.

Options:
  --region REGION         AWS region (default: \$REGION or us-east-1)
  --project NAME          Project tag value used for discovery (default: \$PROJECT or agentic-demo)
  --instance-id ID        EC2 InstanceId to start (overrides discovery)
  --name NAME             EC2 Name tag (default fallback: <project>-gpu)
  --no-wait               Do not wait for running state (default: wait)

Discovery order when --instance-id not provided:
  1) aws/out/ec2-windows-gpu.outputs.json (CloudFormation outputs)
  2) DescribeInstances by Name tag (--name or \${PROJECT}-gpu), platform=windows
  3) DescribeInstances by Project tag (\${PROJECT}), platform=windows

Examples:
  bash aws/scripts/start-ec2-windows.sh
  REGION=us-east-1 PROJECT=agentic-demo bash aws/scripts/start-ec2-windows.sh
  bash aws/scripts/start-ec2-windows.sh --instance-id i-04bcee1a80b8c7839

USAGE
  exit 2
}

need aws
need jq

REGION="${REGION:-us-east-1}"
PROJECT="${PROJECT:-agentic-demo}"
OUT_DIR="aws/out"
OUT_EC2="$OUT_DIR/ec2-windows-gpu.outputs.json"
INSTANCE_ID=""
INSTANCE_NAME=""
WAIT_FOR_RUNNING=1

# --- Parse args ---
while [[ $# -gt 0 ]]; do
  case "$1" in
    --region) REGION="$2"; shift 2;;
    --project) PROJECT="$2"; shift 2;;
    --instance-id) INSTANCE_ID="$2"; shift 2;;
    --name) INSTANCE_NAME="$2"; shift 2;;
    --no-wait) WAIT_FOR_RUNNING=0; shift 1;;
    -h|--help) usage;;
    *) err "Unknown argument: $1"; usage;;
  esac
done

# --- Resolve instance id if not provided ---
resolve_instance_id() {
  local id=""
  # 1) outputs file
  if [[ -z "${INSTANCE_ID}" ]] && [[ -f "$OUT_EC2" ]]; then
    id="$(jq -r '.[] | select(.OutputKey=="InstanceId") | .OutputValue' "$OUT_EC2" 2>/dev/null | head -n1 || true)"
  fi

  # 2) by Name tag
  if [[ -z "$id" ]]; then
    local name="${INSTANCE_NAME:-${PROJECT}-gpu}"
    id="$(aws ec2 describe-instances \
      --region "$REGION" \
      --filters "Name=tag:Name,Values=${name}" "Name=platform,Values=windows" "Name=instance-state-name,Values=pending,running,stopping,stopped" \
      --query 'Reservations[].Instances[].InstanceId' --output text 2>/dev/null | tr '\t' '\n' | head -n1 || true)"
  fi

  # 3) by Project tag
  if [[ -z "$id" ]]; then
    id="$(aws ec2 describe-instances \
      --region "$REGION" \
      --filters "Name=tag:Project,Values=${PROJECT}" "Name=platform,Values=windows" "Name=instance-state-name,Values=pending,running,stopping,stopped" \
      --query 'Reservations[].Instances[].InstanceId' --output text 2>/dev/null | tr '\t' '\n' | head -n1 || true)"
  fi

  echo -n "$id"
}

if [[ -z "$INSTANCE_ID" ]]; then
  INSTANCE_ID="$(resolve_instance_id || true)"
fi
if [[ -z "$INSTANCE_ID" || "$INSTANCE_ID" == "None" ]]; then
  err "Unable to determine InstanceId. Provide --instance-id or ensure $OUT_EC2 exists or tags are set."
  exit 2
fi

echo "Starting EC2 instance: $INSTANCE_ID (region=$REGION)"
aws ec2 start-instances --region "$REGION" --instance-ids "$INSTANCE_ID" >/dev/null

if [[ $WAIT_FOR_RUNNING -eq 1 ]]; then
  echo "Waiting for instance to reach running state..."
  aws ec2 wait instance-running --region "$REGION" --instance-ids "$INSTANCE_ID"
fi

echo "Instance status:"
aws ec2 describe-instances \
  --region "$REGION" \
  --instance-ids "$INSTANCE_ID" \
  --query 'Reservations[].Instances[].{Id:InstanceId,Type:InstanceType,State:State.Name,PublicIp:PublicIpAddress,PublicDns:PublicDnsName,Az:Placement.AvailabilityZone,Name:Tags[?Key==`Name`]|[0].Value,Project:Tags[?Key==`Project`]|[0].Value}' \
  --output json

echo
echo "Connection hint:"
echo "  - Use Microsoft Remote Desktop (RDP 3389)"
echo "  - Username: Administrator"
echo "  - Decrypt password in EC2 console (Get Password) using your KeyPair if needed"
echo "  - Note: Public IP changes each stop/start unless you attach an Elastic IP"
echo
echo "Tip: To stop later and save costs, use: aws ec2 stop-instances --region \"$REGION\" --instance-ids \"$INSTANCE_ID\""