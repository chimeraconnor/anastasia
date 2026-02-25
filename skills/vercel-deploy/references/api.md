# Vercel API Reference

## Authentication

All API requests require Bearer token:
```
Authorization: Bearer {VERCEL_TOKEN}
```

## Projects API (v9)

### Create Project
```
POST https://api.vercel.com/v9/projects
```

Request body:
```json
{
  "name": "my-project",
  "gitRepository": {
    "type": "github",
    "repo": "owner/repo"
  },
  "framework": "nextjs",
  "buildCommand": "next build",
  "installCommand": "npm install",
  "outputDirectory": null
}
```

Response includes `id` (project ID) and `link` details.

### Update Project
```
PATCH https://api.vercel.com/v9/projects/{project_id}
```

Common updates:

**Remove SSO protection (make public):**
```json
{"ssoProtection": null}
```

**Set output directory:**
```json
{"outputDirectory": "dist"}
```

**Enable public source:**
```json
{"publicSource": true}
```

### Get Project
```
GET https://api.vercel.com/v9/projects/{project_id}
```

## Deployments API (v13)

### Create Deployment
```
POST https://api.vercel.com/v13/deployments
```

Request body:
```json
{
  "name": "my-project",
  "public": true,
  "gitSource": {
    "type": "github",
    "repo": "owner/repo",
    "ref": "master",
    "repoId": 123456789
  },
  "project": "prj_xxxx",
  "target": "production"
}
```

### Get Deployment Status
```
GET https://api.vercel.com/v13/deployments/{deployment_id}
```

Check `readyState`: `INITIALIZING` → `BUILDING` → `READY` or `ERROR`

### List Deployments
```
GET https://api.vercel.com/v6/deployments?projectId={project_id}
```

## User API (v1)

### Get Current User
```
GET https://api.vercel.com/v1/user
```

Returns user info including `defaultTeamId`.

## Response Fields

### Deployment Response

Key fields:
- `id` - Deployment ID
- `url` - Direct deployment URL (with hash)
- `alias` - Array of assigned aliases
- `readyState` - Current status
- `public` - Whether deployment is public

### Project Response

Key fields:
- `id` - Project ID (prj_xxx)
- `name` - Project name
- `link` - Git repository connection details
- `framework` - Detected framework

## Error Codes

- `bad_request` - Invalid request format or missing fields
- `invalid_sso_protection` - Invalid SSO configuration
- `NEXT_NO_ROUTES_MANIFEST` - Next.js build configuration issue

## Framework Values

- `nextjs` - Next.js
- `react` - Create React App
- `vue` - Vue.js
- `nuxtjs` - Nuxt.js
- `svelte` - Svelte
- `angular` - Angular
- `ember` - Ember
- `hugo` - Hugo
- `jekyll` - Jekyll
- `gatsby` - Gatsby
- `remix` - Remix
- `astro` - Astro
- `hexo` - Hexo
- `docusaurus` - Docusaurus
- `preact` - Preact
- `solidstart` - SolidStart
- `dojo` - Dojo
- `sapper` - Sapper
- `ionic-react` - Ionic React
- `ionic-angular` - Ionic Angular
- `ionic-vue` - Ionic Vue
- `parcel` - Parcel
- `polymer` - Polymer
- `create-react-app` - Create React App
- `gridsome` - Gridsome
- `umijs` - UmiJS
- `sveltekit` - SvelteKit
- `storybook` - Storybook
- `brunch` - Brunch
- `middleman` - Middleman
- `zola` - Zola
- `hydrogen` - Hydrogen
- `vite` - Vite
- `vuepress` - VuePress
- `docusaurus-v2` - Docusaurus v2
- `sanity` - Sanity
- `seed` - Seed
- `scully` - Scully
- `mkdocs` - MkDocs
- `sveltekit-1` - SvelteKit 1.0
- `alpine` - Alpine.js
- `docusaurus-v3` - Docusaurus v3
