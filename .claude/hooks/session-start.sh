#!/bin/bash
set -euo pipefail

# Claude Code Session Start Hook for ecosystem repository
# This script installs dependencies and prepares the environment for web sessions
# Installs in the background to avoid blocking session startup

# Only run in remote Claude Code web sessions
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Return async mode to allow session to start while dependencies install
echo '{"async": true, "asyncTimeout": 300000}'

# Get project directory
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"

# Install pnpm dependencies
echo "Installing dependencies with pnpm..."
cd "$PROJECT_DIR"
pnpm install --frozen-lockfile

# Add Supabase dependency if not already present
echo "Ensuring Supabase client library is installed..."
pnpm add @supabase/supabase-js

# Build the project to prepare for linting and testing
echo "Building project..."
pnpm run build

# Verify TypeScript compilation works
echo "Verifying TypeScript compilation..."
pnpm run check

echo "✅ Session startup hook completed successfully!"
