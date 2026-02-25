#!/bin/bash
# Make a Vercel project public (remove SSO protection)

set -e

PROJECT_ID="${1:-}"

if [ -z "$PROJECT_ID" ]; then
  echo "Usage: $0 <project-id>"
  echo "Example: $0 prj_abc123xyz"
  echo ""
  echo "To find project ID:"
  echo "  curl -H 'Authorization: Bearer \$VERCEL_TOKEN' https://api.vercel.com/v9/projects/my-project-name"
  exit 1
fi

# Load token
if [ -f ".env.vercel" ]; then
  export $(cat .env.vercel | grep -v '^#' | xargs)
fi

if [ -z "$VERCEL_TOKEN" ]; then
  echo "Error: VERCEL_TOKEN not found. Set it in .env.vercel or environment."
  exit 1
fi

echo "Making project public: $PROJECT_ID"

RESPONSE=$(curl -s -X PATCH "https://api.vercel.com/v9/projects/$PROJECT_ID" \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ssoProtection": null}')

if echo "$RESPONSE" | grep -q '"error"'; then
  echo "Error:"
  echo "$RESPONSE" | grep -o '"message":"[^"]*"' | head -1
  exit 1
fi

echo "✅ Project is now public (SSO protection removed)"
