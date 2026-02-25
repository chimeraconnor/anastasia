#!/bin/bash
# Deploy a project to Vercel

set -e

PROJECT_NAME="${1:-}"
REPO="${2:-}"
REPO_ID="${3:-}"
TARGET="${4:-production}"

if [ -z "$PROJECT_NAME" ] || [ -z "$REPO" ]; then
  echo "Usage: $0 <project-name> <owner/repo> [repo-id] [target]"
  echo "Example: $0 my-site chimeraconnor/my-site 123456789 production"
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

# Get project ID if not known
PROJECT_RESPONSE=$(curl -s "https://api.vercel.com/v9/projects/$PROJECT_NAME" \
  -H "Authorization: Bearer $VERCEL_TOKEN")

if echo "$PROJECT_RESPONSE" | grep -q '"error"'; then
  echo "Error: Project '$PROJECT_NAME' not found. Create it first."
  exit 1
fi

PROJECT_ID=$(echo "$PROJECT_RESPONSE" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

# Get repo ID if not provided
if [ -z "$REPO_ID" ]; then
  # Try to extract from GitHub or use a placeholder
  echo "Warning: repo-id not provided, deployment may fail"
  REPO_ID="null"
else
  REPO_ID="\"$REPO_ID\""
fi

echo "Deploying: $PROJECT_NAME"
echo "Project ID: $PROJECT_ID"
echo "Repo: $REPO"
echo "Target: $TARGET"

# Create deployment
RESPONSE=$(curl -s -X POST "https://api.vercel.com/v13/deployments" \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"$PROJECT_NAME\",
    \"public\": true,
    \"gitSource\": {
      \"type\": \"github\",
      \"repo\": \"$REPO\",
      \"ref\": \"master\",
      \"repoId\": $REPO_ID
    },
    \"project\": \"$PROJECT_ID\",
    \"target\": \"$TARGET\"
  }")

# Check for errors
if echo "$RESPONSE" | grep -q '"error"'; then
  echo "Error creating deployment:"
  echo "$RESPONSE" | grep -o '"message":"[^"]*"' | head -1
  exit 1
fi

DEPLOYMENT_ID=$(echo "$RESPONSE" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
URL=$(echo "$RESPONSE" | grep -o '"url":"[^"]*"' | head -1 | cut -d'"' -f4)
ALIAS=$(echo "$RESPONSE" | grep -o '"alias":\[[^]]*\]' | grep -o '"[^"]*vercel.app"' | head -1 | tr -d '"')

echo "✅ Deployment created: $DEPLOYMENT_ID"
echo "URL: https://$URL"
[ -n "$ALIAS" ] && echo "Alias: https://$ALIAS"

# Wait for deployment
echo "Waiting for deployment to complete..."
for i in {1..30}; do
  sleep 5
  STATUS=$(curl -s "https://api.vercel.com/v13/deployments/$DEPLOYMENT_ID" \
    -H "Authorization: Bearer $VERCEL_TOKEN" | grep -o '"readyState":"[^"]*"' | head -1 | cut -d'"' -f4)
  
  echo "  Status: $STATUS"
  
  if [ "$STATUS" = "READY" ]; then
    echo "✅ Deployment complete!"
    echo "Live URL: https://$ALIAS"
    exit 0
  elif [ "$STATUS" = "ERROR" ]; then
    echo "❌ Deployment failed"
    exit 1
  fi
done

echo "⚠️ Deployment is taking longer than expected. Check manually:"
echo "https://vercel.com/dashboard/$PROJECT_NAME"
