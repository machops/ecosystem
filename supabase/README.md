# Supabase Configuration

This directory contains Supabase configuration and migration files for the ecosystem application.

## Directory Structure

```
supabase/
├── config.toml                 # Supabase local development configuration
├── migrations/                 # Database migration files
│   └── 001_init.sql          # Initial schema setup
├── seed.sql                    # Development seed data
└── README.md                   # This file
```

## Setup

### 1. Install Supabase CLI

```bash
npm install -g supabase
```

### 2. Link to Your Project

```bash
supabase link --project-ref your-project-id
```

### 3. Local Development

Start local Supabase stack:

```bash
supabase start
```

This will start:
- PostgreSQL database on port 5432
- Supabase Studio on http://localhost:54323
- Auth service on port 54321
- Realtime on port 54322
- Inbucket (email testing) on port 54324

### 4. Create a Migration

After making schema changes in Supabase Studio, pull them locally:

```bash
supabase db pull
```

This creates a new migration file in `migrations/`.

## Migrations

Database migrations are SQL files in the `migrations/` directory.

### Create a New Migration

```bash
supabase migration new migration_name
```

This creates a timestamped SQL file.

### Apply Migrations

Locally (running migrations on local Supabase):
```bash
supabase db push
```

To production:
```bash
supabase db push --linked
```

## Seed Data

The `seed.sql` file contains test data for development. It's automatically applied during local development setup.

To manually apply seeds:

```bash
psql postgresql://postgres:postgres@localhost:5432/postgres -f supabase/seed.sql
```

## Environment Variables

Required environment variables for Supabase:

```bash
# Client-side (public)
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=sb_publishable_...

# Server-side (secret)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Copy `.env.example` to `.env.local` and fill in your Supabase project credentials.

## Schema

### Users Table
- `id`: UUID primary key
- `open_id`: Unique identifier from OAuth
- `name`: User display name
- `email`: User email address
- `login_method`: OAuth method used
- `role`: 'user' or 'admin'
- `last_signed_in`: Last authentication timestamp
- `created_at`: Account creation timestamp
- `updated_at`: Last update timestamp

### Audit Logs Table
- `id`: UUID primary key
- `user_id`: Reference to users table
- `action`: Action performed
- `resource_type`: Type of resource modified
- `resource_id`: ID of modified resource
- `changes`: JSON object of changes
- `created_at`: Timestamp of action

### Sessions Table
- `id`: UUID primary key
- `user_id`: Reference to users table
- `token_hash`: Hash of session token
- `expires_at`: Session expiration time
- `created_at`: Session creation time
- `ip_address`: Client IP address
- `user_agent`: Client browser info

### Notification Preferences Table
- `id`: UUID primary key
- `user_id`: Reference to users table
- `email_enabled`: Email notifications enabled
- `push_enabled`: Push notifications enabled
- `sms_enabled`: SMS notifications enabled
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

## Row Level Security (RLS)

RLS is enabled on all tables. Policies ensure:

1. Users can only access their own data
2. Admins can access all user data
3. Audit logs are restricted by user access

Modify policies in the Supabase Studio dashboard or in `migrations/`.

## Using Supabase in Code

### Client-side
```typescript
import { supabase } from '@shared/supabase';

const { data: users } = await supabase
  .from('users')
  .select('*');
```

### Server-side
```typescript
import { supabaseAdmin } from '@shared/supabase/server';

const { data: users } = await supabaseAdmin
  .from('users')
  .select('*');
```

### Real-time Subscriptions
```typescript
import { useRealtimeSubscription } from '@shared/supabase/hooks';

function UserList() {
  const { data: users } = useRealtimeSubscription('users');
  return <div>{users.map(u => <div key={u.id}>{u.name}</div>)}</div>;
}
```

## Cleanup

Stop local Supabase stack:

```bash
supabase stop
```

## Documentation

- [Supabase Documentation](https://supabase.com/docs)
- [Supabase CLI Reference](https://supabase.com/docs/reference/cli/introduction)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
