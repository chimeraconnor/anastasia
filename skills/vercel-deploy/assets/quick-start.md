# Quick Start Template

## Complete Workflow Example

```bash
# 1. Create Next.js project
cd ~/workspace/projects
npx create-next-app@latest my-site --typescript --tailwind --eslint --app --src-dir --import-alias "@/*" --use-npm --yes

# 2. Initialize git and push
cd my-site
git init
git add .
git commit -m "Initial commit"
gh repo create my-site --private --source=. --push

# 3. Get repo ID from GitHub API
REPO_ID=$(curl -s "https://api.github.com/repos/chimeraconnor/my-site" | grep -o '"id": [0-9]*' | head -1 | cut -d' ' -f2)

# 4. Create Vercel project
export VERCEL_TOKEN=$(cat ~/.env.vercel | grep VERCEL_TOKEN | cut -d= -f2)
curl -s -X POST "https://api.vercel.com/v9/projects" \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"my-site\",
    \"gitRepository\": {
      \"type\": \"github\",
      \"repo\": \"chimeraconnor/my-site\"
    },
    \"framework\": \"nextjs\"
  }"

# 5. Deploy
curl -s -X POST "https://api.vercel.com/v13/deployments" \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"my-site\",
    \"public\": true,
    \"gitSource\": {
      \"type\": \"github\",
      \"repo\": \"chimeraconnor/my-site\",
      \"ref\": \"master\",
      \"repoId\": $REPO_ID
    },
    \"target\": \"production\"
  }"

# 6. Make public (if needed)
PROJECT_ID=$(curl -s "https://api.vercel.com/v9/projects/my-site" -H "Authorization: Bearer $VERCEL_TOKEN" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
curl -s -X PATCH "https://api.vercel.com/v9/projects/$PROJECT_ID" \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ssoProtection": null}'
```

## One-Liner Commands

**Create + Deploy (after token is set):**
```bash
# Set these variables
PROJECT_NAME="my-site"
REPO="chimeraconnor/my-site"
REPO_ID="123456789"

# Create project
curl -s -X POST "https://api.vercel.com/v9/projects" \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"$PROJECT_NAME\",\"gitRepository\":{\"type\":\"github\",\"repo\":\"$REPO\"},\"framework\":\"nextjs\"}"

# Deploy
curl -s -X POST "https://api.vercel.com/v13/deployments" \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"$PROJECT_NAME\",\"public\":true,\"gitSource\":{\"type\":\"github\",\"repo\":\"$REPO\",\"ref\":\"master\",\"repoId\":$REPO_ID},\"target\":\"production\"}"
```

## Getting Repo ID

GitHub API:
```bash
curl -s "https://api.github.com/repos/OWNER/REPO" | grep -o '"id": [0-9]*' | head -1 | cut -d' ' -f2
```

Or from Vercel after linking:
```bash
curl -s "https://api.vercel.com/v9/projects/PROJECT-NAME" \
  -H "Authorization: Bearer $VERCEL_TOKEN" | grep -o '"repoId":[0-9]*' | head -1 | cut -d: -f2
```
