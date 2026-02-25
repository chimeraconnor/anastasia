#!/bin/bash
# Create a Vercel project linked to a GitHub repository

set -e

PROJECT_NAME="${1:-}"
REPO="${2:-}"
FRAMEWORK="${3:-nextjs}"

if [ -z "$PROJECT_NAME" ] || [ -z "$REPO" ]; then
  echo "Usage: $0 <project-name> <owner/repo> [framework]"
  echo "Example: $0 my-site chimeraconnor/my-site nextjs"
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

echo "Creating Vercel project: $PROJECT_NAME"
echo "Linking to GitHub repo: $REPO"
echo "Framework: $FRAMEWORK"

RESPONSE=$(curl -s -X POST "https://api.vercel.com/v9/projects" \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"$PROJECT_NAME\",
    \"gitRepository\": {
      \"type\": \"github\",
      \"repo\": \"$REPO\"
    },
    \"framework\": \"$FRAMEWORK\",
    \"buildCommand\": \"next build\",
    \"installCommand\": \"npm install\",
    \"outputDirectory\": null
  }")

# Check for errors
if echo "$RESPONSE" | grep -q '"error"'; then
  echo "Error creating project:"
  echo "$RESPONSE" | grep -o '"message":"[^"]*"' | head -1
  exit 1
fi

PROJECT_ID=$(echo "$RESPONSE" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

echo "✅ Project created: $PROJECT_ID"
echo "Project URL: https://vercel.com/dashboard/$PROJECT_NAME"
