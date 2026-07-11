#!/usr/bin/env bash
# Creates the first admin user by calling the running API.
# Usage: ./scripts/create_admin.sh admin@example.com "Admin Name" "StrongPassword123"
set -e

API_URL="${API_URL:-http://localhost:8000/api/v1}"
EMAIL="${1:?Usage: create_admin.sh <email> <full_name> <password>}"
FULL_NAME="${2:?Usage: create_admin.sh <email> <full_name> <password>}"
PASSWORD="${3:?Usage: create_admin.sh <email> <full_name> <password>}"

curl -s -X POST "$API_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"full_name\":\"$FULL_NAME\",\"password\":\"$PASSWORD\",\"role\":\"admin\"}" \
  | python3 -m json.tool

echo "Admin user created (or already existed). You can now log in at /login."
