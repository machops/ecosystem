# Cloudflare Workers Configuration

This directory contains Cloudflare Workers configuration and deployment templates for the ecosystem application frontend.

## Directory Structure

```
cloudflare/
├── frontend/
│   ├── projects/                    # Placeholder for additional projects
│   ├── project-01/                  # Project 1 Worker
│   │   ├── wrangler.toml           # Project configuration
│   │   ├── package.json            # Dependencies
│   │   ├── src/
│   │   │   └── index.ts            # Worker entry point
│   │   └── tsconfig.json           # TypeScript config
│   ├── project-02/                  # Project 2 Worker
│   ├── project-03/                  # Project 3 Worker
│   ├── project-04/                  # Project 4 Worker
│   ├── project-05/                  # Project 5 Worker
│   └── project-06/                  # Project 6 Worker
└── README.md                        # This file
```

## Architecture Design

### Why This Structure Works

**Scalability:**
- Each project is **self-contained** with its own dependencies and configuration
- Adding new projects (project-07, project-08, etc.) is straightforward
- Projects can be deployed independently without affecting others

**Flexibility:**
- Each project has its own `wrangler.toml` for independent configuration
- Environment variables and secrets are project-specific
- Different deployment pipelines per project are supported

**Maintainability:**
- Clear separation of concerns
- Easy to locate and update project-specific code
- Shared tooling in root directory (optional)

### Alternative Structures Considered

**Monorepo with Root Config:**
```
cloudflare/
├── wrangler.toml    # Single config for all projects
├── src/
│   ├── project-01/
│   ├── project-02/
│   └── ...
```
❌ Less flexible, harder to scale independently

**Subdirectories by Type:**
```
cloudflare/
├── apis/           # API workers
├── pages/          # Page handlers
├── middleware/     # Middleware workers
```
❌ Harder to organize growing projects

**Chosen: Project-Based Organization**
```
cloudflare/
├── frontend/
│   ├── project-01/
│   ├── project-02/
│   └── ...
```
✅ Clear, scalable, maintainable

## Quick Start

### 1. Install Wrangler CLI

```bash
npm install -g wrangler
# or
pnpm add -g wrangler
```

### 2. Configure Project

Navigate to a project directory and set up configuration:

```bash
cd cloudflare/frontend/project-01

# Initialize Wrangler (if needed)
wrangler init

# Edit wrangler.toml with your account details
```

### 3. Deploy to Development

```bash
wrangler dev
```

This starts a local development server at `http://localhost:8787`

### 4. Deploy to Production

```bash
# Deploy to default environment
wrangler deploy

# Or deploy to specific environment
wrangler deploy --env production
wrangler deploy --env staging
```

## Configuration Guide

### wrangler.toml Structure

Each project's `wrangler.toml` includes:

```toml
name = "project-01"                    # Worker name
type = "javascript"                    # Project type
account_id = "your_account_id"        # Cloudflare account
workers_dev = true                     # Enable workers.dev subdomain

[env.production]
name = "project-01-prod"              # Production name
route = "api.example.com/project-01/*" # Production route
zone_id = "your_zone_id"              # Production zone

[env.staging]
name = "project-01-staging"           # Staging name
route = "staging-api.example.com/*"   # Staging route
zone_id = "your_zone_id"              # Staging zone

[[kv_namespaces]]
binding = "KV_STORAGE"                # Variable name in code
id = "your_kv_namespace_id"           # Production KV ID
preview_id = "your_preview_kv_id"     # Preview KV ID

[[r2_buckets]]
binding = "R2_BUCKET"                 # Variable name in code
bucket_name = "project-01-bucket"     # Bucket name
```

### Environment Setup

#### 1. Get Your Account ID

```bash
wrangler whoami
```

This displays your Cloudflare account ID.

#### 2. Create KV Namespaces

```bash
wrangler kv:namespace create "storage"
wrangler kv:namespace create "storage" --preview
```

Copy the IDs into `wrangler.toml`

#### 3. Create R2 Buckets

```bash
wrangler r2 bucket create "project-01-bucket"
```

### Environment Variables

Create `.env.local` in each project:

```env
# Development
ENVIRONMENT=development
API_URL=http://localhost:8000

# Production
ENVIRONMENT=production
API_URL=https://api.example.com
```

Reference in code:

```typescript
const env = process.env.ENVIRONMENT;
```

## Worker Development

### Basic Worker Structure

```typescript
export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);

    // Route requests
    if (url.pathname.startsWith('/api/')) {
      return handleAPI(request, env);
    }

    // Handle other routes
    return new Response('Hello World');
  },
};

async function handleAPI(request: Request, env: Env): Promise<Response> {
  return new Response(JSON.stringify({ message: 'API' }), {
    headers: { 'Content-Type': 'application/json' },
  });
}

interface Env {
  KV_STORAGE: KVNamespace;
  R2_BUCKET: R2Bucket;
}
```

### Using KV Storage

```typescript
async function getFromCache(key: string, env: Env): Promise<string | null> {
  const value = await env.KV_STORAGE.get(key);
  return value;
}

async function setInCache(key: string, value: string, env: Env) {
  await env.KV_STORAGE.put(key, value, { expirationTtl: 3600 });
}
```

### Using R2 Storage

```typescript
async function uploadFile(file: ArrayBuffer, name: string, env: Env) {
  await env.R2_BUCKET.put(name, file, {
    httpMetadata: { contentType: 'application/octet-stream' },
  });
}

async function downloadFile(name: string, env: Env) {
  const object = await env.R2_BUCKET.get(name);
  return object?.arrayBuffer();
}
```

## Deployment Strategy

### Multi-Environment Deployment

```bash
# Deploy to staging for testing
cd cloudflare/frontend/project-01
wrangler deploy --env staging

# Verify functionality, then deploy to production
wrangler deploy --env production
```

### CI/CD Integration

Add to your CI/CD pipeline:

```yaml
deploy-cloudflare:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v3

    - name: Install dependencies
      run: |
        cd cloudflare/frontend/project-01
        npm install

    - name: Deploy to Cloudflare
      run: |
        cd cloudflare/frontend/project-01
        npx wrangler deploy --env production
      env:
        CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
        CLOUDFLARE_ACCOUNT_ID: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
```

## Adding New Projects

### 1. Create Directory Structure

```bash
mkdir -p cloudflare/frontend/project-07/{src}
```

### 2. Copy Template Files

```bash
cp cloudflare/frontend/project-01/wrangler.toml cloudflare/frontend/project-07/
cp cloudflare/frontend/project-01/package.json cloudflare/frontend/project-07/
cp cloudflare/frontend/project-01/src/index.ts cloudflare/frontend/project-07/src/
```

### 3. Update Configuration

Edit `cloudflare/frontend/project-07/wrangler.toml`:
- Change `name` from `project-01` to `project-07`
- Update bucket names and KV namespaces
- Update routes if needed

### 4. Deploy

```bash
cd cloudflare/frontend/project-07
wrangler deploy
```

## Monitoring & Analytics

### View Analytics

```bash
# View analytics for a worker
wrangler analytics get
```

### Real-time Logs

```bash
# Stream real-time logs
wrangler tail --format pretty
```

### Custom Metrics

```typescript
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const startTime = Date.now();

    // Process request
    const response = await handleRequest(request, env);

    // Track metrics
    const duration = Date.now() - startTime;
    console.log(`Request processed in ${duration}ms`);

    return response;
  },
};
```

## Troubleshooting

### "Invalid Account ID"

```bash
# Verify your account ID
wrangler whoami

# Update wrangler.toml with correct ID
# Then retry
wrangler deploy
```

### "KV Namespace Not Found"

```bash
# List your KV namespaces
wrangler kv:namespace list

# Create if missing
wrangler kv:namespace create "storage"

# Update wrangler.toml with correct ID
```

### "Route Conflict"

Routes in `wrangler.toml` must be unique across all workers in the same zone.

```toml
# ✅ Good - different paths
route = "api.example.com/project-01/*"
route = "api.example.com/project-02/*"

# ❌ Bad - conflicting routes
route = "api.example.com/*"
route = "api.example.com/project-01/*"
```

## Performance Best Practices

### 1. Cache Static Content

```typescript
const cache = new Map<string, Response>();

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (cache.has(request.url)) {
      return cache.get(request.url)!;
    }

    const response = await handleRequest(request, env);
    cache.set(request.url, response.clone());
    return response;
  },
};
```

### 2. Use Edge Cache

```typescript
const response = new Response('Cached content', {
  headers: {
    'Cache-Control': 'public, max-age=3600',
  },
});
```

### 3. Batch KV Operations

```typescript
// ❌ Slow - individual operations
for (const key of keys) {
  await env.KV_STORAGE.get(key);
}

// ✅ Fast - batch operations where possible
const promises = keys.map(key => env.KV_STORAGE.get(key));
await Promise.all(promises);
```

## Resources

- [Cloudflare Workers Documentation](https://developers.cloudflare.com/workers/)
- [Wrangler CLI Reference](https://developers.cloudflare.com/workers/wrangler/)
- [KV Storage Guide](https://developers.cloudflare.com/workers/runtime-apis/kv/)
- [R2 Object Storage](https://developers.cloudflare.com/r2/)
- [Environment Variables](https://developers.cloudflare.com/workers/configuration/environment-variables/)

## Support

For issues or questions:
1. Check [Cloudflare Community](https://community.cloudflare.com/)
2. Review [Cloudflare Status](https://www.cloudflarestatus.com/)
3. Open issue in this repository

---

**Last Updated**: 2026-02-18
**Status**: Production Ready
