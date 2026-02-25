---
name: vercel-deploy
description: Deploy websites to Vercel with GitHub integration. Use when: (1) Creating new web projects and deploying them, (2) Setting up automatic deployments from GitHub repos, (3) Managing Vercel projects and domains, (4) Configuring deployment settings. Handles full workflow: GitHub repo creation → Vercel project setup → deployment → domain configuration.
---

# Vercel Deployment Skill

Complete workflow for deploying websites to Vercel with GitHub integration.

## Prerequisites

- GitHub CLI (`gh`) authenticated
- Vercel token stored in `.env.vercel` as `VERCEL_TOKEN`
- Node.js/npm available for project scaffolding

## Quick Start

### 1. Create and Deploy a New Project

```bash
# Create project locally
npx create-next-app@latest my-site --typescript --tailwind --eslint --app --src-dir --import-alias "@/*" --use-npm --yes

# Initialize git and push to GitHub
cd my-site
git init
git add .
git commit -m "Initial commit"
gh repo create my-site --private --source=. --push

# Create Vercel project and deploy
./scripts/create-vercel-project.sh my-site chimeraconnor/my-site
./scripts/deploy.sh my-site
```

### 2. Deploy Existing GitHub Repo

```bash
./scripts/create-vercel-project.sh my-site chimeraconnor/my-site
./scripts/deploy.sh my-site
```

## Token Storage

Store Vercel token in workspace root:
```
.env.vercel:
VERCEL_TOKEN=vcp_...
```

Load it in scripts: `export $(cat .env.vercel | xargs)`

## Common Tasks

### Make Deployment Public

By default Vercel projects have SSO protection. To make public:

```bash
export VERCEL_TOKEN=...
curl -s -X PATCH "https://api.vercel.com/v9/projects/{project_id}" \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ssoProtection": null}'
```

### Get Clean URL (without team slug)

Vercel auto-assigns: `project-name-team-slug.vercel.app`

The alias without team slug is usually: `project-name.vercel.app`

Check aliases on deployment and share the cleanest one.

### Configure Next.js for Vercel

Default `next.config.ts` works. Don't set `output: 'export'` unless doing static sites.

## API Endpoints

See [references/api.md](references/api.md) for full API documentation.

Key endpoints:
- `POST /v9/projects` - Create project
- `POST /v13/deployments` - Trigger deployment
- `GET /v13/deployments/{id}` - Check status
- `PATCH /v9/projects/{id}` - Update project settings

## Troubleshooting

**"Authentication required" error:**
- Project has SSO protection enabled
- Run: `curl -X PATCH ... -d '{"ssoProtection": null}'`

**Build fails with "routes-manifest.json" missing:**
- Remove `output: 'export'` from next.config.ts
- Vercel uses server-side rendering by default

**"Invalid API version" error:**
- Use `/v9/` for projects, `/v13/` for deployments
- Check [references/api.md](references/api.md) for correct versions

## Project Structure

After creation, projects have:
- GitHub repo with source code
- Vercel project linked to repo
- Auto-deploy on push to production branch
- Production URL (alias)

## Scripts

All scripts are in `scripts/`:
- `create-vercel-project.sh` - Create Vercel project linked to GitHub
- `deploy.sh` - Trigger deployment and wait for completion
- `make-public.sh` - Remove SSO protection
