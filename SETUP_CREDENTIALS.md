# Environment Credentials Setup Guide

**IMPORTANT: Keep these credentials secure and never commit them to version control!**

## 1. Supabase Configuration

Your Supabase project has been created successfully.

### Project Details
- **Project Name:** autoecoops
- **Project ID:** yrfxijooswpvdpdseswy
- **API URL:** https://yrfxijooswpvdpdseswy.supabase.co
- **Region:** ap-south-1

### Update .env.local

Add these credentials to `.env.local` (already in `.gitignore`):

```env
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://yrfxijooswpvdpdseswy.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlyZnhpam9vc3dwdmRwZHNlc3d5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA3MjYxNjMsImV4cCI6MjA4NjMwMjE2M30.R4gO5Kj5G0aYnvOE3N4D3gBN1Zu7fD9d31z99qW023I

# Server-side only (NEVER expose to browser)
SUPABASE_URL=https://yrfxijooswpvdpdseswy.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlyZnhpam9vc3dwdmRwZHNlc3d5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MDcyNjE2MywiZXhwIjoyMDg2MzAyMTYzfQ.-OGp0mC6K3iJzk5-oWl6LsbQpkBwk8yTPMa-hEL74MQ
```

### Next Steps
1. Update `.env.local` with credentials above
2. Restart your development server: `pnpm dev`
3. Supabase will be ready to use in your application

## 2. Cloudflare Workers Configuration

Your Cloudflare API token has been created.

### Credentials
- **Account ID:** 2fead4a141ec2c677eb3bf0ac535f1d5
- **API Token:** uzmzqUoqAFhSH7J3e-pupgjgKA0sDEf1ZzVC53JK

### Configure Wrangler

1. **Login to Cloudflare via Wrangler:**
```bash
wrangler login
```

2. **Or set API Token in environment:**
```bash
export CLOUDFLARE_API_TOKEN=uzmzqUoqAFhSH7J3e-pupgjgKA0sDEf1ZzVC53JK
```

3. **Update each project's wrangler.toml** with your account ID:
```toml
account_id = "2fead4a141ec2c677eb3bf0ac535f1d5"
```

### Update .env.local (Optional)
For CI/CD pipelines, add:
```env
CLOUDFLARE_API_TOKEN=uzmzqUoqAFhSH7J3e-pupgjgKA0sDEf1ZzVC53JK
CLOUDFLARE_ACCOUNT_ID=2fead4a141ec2c677eb3bf0ac535f1d5
```

### Next Steps
1. Navigate to a Cloudflare project: `cd cloudflare/frontend/project-01`
2. Test connection: `wrangler deploy --dry-run`
3. Deploy worker: `wrangler deploy`

## 3. Security Best Practices

### ✅ Do's
- ✅ Store credentials in `.env.local` (git-ignored)
- ✅ Use different credentials per environment (dev, staging, prod)
- ✅ Rotate API tokens regularly
- ✅ Use service role key only in server-side code
- ✅ Store secrets in CI/CD platform (GitHub Actions, CircleCI)

### ❌ Don'ts
- ❌ Never commit `.env.local` to git
- ❌ Never expose service role key to browser
- ❌ Never share credentials via chat/email
- ❌ Never hardcode credentials in source code
- ❌ Never use same credentials across environments

## 4. GitHub Actions Setup (For CI/CD)

Add these secrets to your GitHub repository:

**Settings → Secrets and variables → Actions**

```
SUPABASE_URL = https://yrfxijooswpvdpdseswy.supabase.co
SUPABASE_SERVICE_ROLE_KEY = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
CLOUDFLARE_API_TOKEN = uzmzqUoqAFhSH7J3e-pupgjgKA0sDEf1ZzVC53JK
CLOUDFLARE_ACCOUNT_ID = 2fead4a141ec2c677eb3bf0ac535f1d5
```

## 5. CircleCI Setup (For CI/CD)

Add these secrets to your CircleCI project:

**Project Settings → Environment Variables**

```
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
CLOUDFLARE_API_TOKEN
CLOUDFLARE_ACCOUNT_ID
```

## 6. Verify Setup

### Test Supabase
```bash
# Will use credentials from .env.local
pnpm dev

# Then in browser console:
import { supabase } from '@shared/supabase'
const { data } = await supabase.from('users').select('*')
console.log(data)
```

### Test Cloudflare
```bash
cd cloudflare/frontend/project-01
wrangler deploy --dry-run
# Should show "Ready to deploy" with no errors
```

## 7. Session Start Hook Status

✅ **Hook is working!** Your session confirmed:
- Dependencies installed automatically
- Supabase client library included
- TypeScript compilation verified
- Ready for development

The hook will run automatically every time you start a Claude Code web session.

---

**Credentials Stored:** 2026-02-18
**Status:** Ready to use
**Next Action:** Update .env.local with credentials above
