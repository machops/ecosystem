# im-integration

Unified IM bot platform supporting WhatsApp, Telegram, LINE, and Messenger.

## Architecture

```
Cloudflare Worker (webhook-router)
        │
        ▼
  API Service (/api/v1/im/webhook)
        │
        ▼
┌───────────────────────────────────────────┐
│         Shared Layer                       │
│  normalizer.ts → router.ts → AI Backend   │
│  (Redis sessions, ECO_* config)            │
└───────────────────────────────────────────┘
        │
        ▼
┌──────┬──────┬──────┬──────────┐
│  WA  │  TG  │ LINE │ Messenger│
│:3002 │:3001 │:3003 │  :3004   │
└──────┴──────┴──────┴──────────┘
```

## Deployment Modes

### Standalone Adapters (recommended for production)

Each channel runs as an independent process:

```bash
# WhatsApp
ECO_WHATSAPP_VERIFY_TOKEN=... ECO_WHATSAPP_ACCESS_TOKEN=... pnpm start:whatsapp

# Telegram
ECO_TELEGRAM_BOT_TOKEN=... pnpm start:telegram

# LINE
ECO_LINE_CHANNEL_SECRET=... ECO_LINE_CHANNEL_ACCESS_TOKEN=... pnpm start:line

# Messenger
ECO_MESSENGER_VERIFY_TOKEN=... ECO_MESSENGER_PAGE_ACCESS_TOKEN=... pnpm start:messenger
```

### Unified Server (development / small deployments)

All channels in a single process on port 4000:

```bash
pnpm start:unified
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `ECO_API_URL` | Yes | Backend API URL |
| `ECO_REDIS_URL` | No | Redis for sessions (default: localhost:6379) |
| `ECO_SERVICE_TOKEN` | No | Bearer token for API auth |
| `ECO_LOG_LEVEL` | No | Log level (default: info) |
| `ECO_IM_SESSION_TTL` | No | Session TTL in seconds (default: 3600) |
| `ECO_WHATSAPP_PORT` | No | WhatsApp adapter port (default: 3002) |
| `ECO_WHATSAPP_VERIFY_TOKEN` | WA | Meta webhook verify token |
| `ECO_WHATSAPP_ACCESS_TOKEN` | WA | Meta Cloud API access token |
| `ECO_WHATSAPP_APP_SECRET` | WA | Meta app secret for signature verification |
| `ECO_WHATSAPP_PHONE_NUMBER_ID` | WA | WhatsApp phone number ID |
| `ECO_TELEGRAM_BOT_TOKEN` | TG | Telegram bot token from BotFather |
| `ECO_TELEGRAM_MODE` | No | polling or webhook (default: polling) |
| `ECO_TELEGRAM_WEBHOOK_URL` | No | Webhook domain for webhook mode |
| `ECO_LINE_PORT` | No | LINE adapter port (default: 3003) |
| `ECO_LINE_CHANNEL_SECRET` | LINE | LINE channel secret |
| `ECO_LINE_CHANNEL_ACCESS_TOKEN` | LINE | LINE channel access token |
| `ECO_MESSENGER_PORT` | No | Messenger adapter port (default: 3004) |
| `ECO_MESSENGER_VERIFY_TOKEN` | FB | Facebook webhook verify token |
| `ECO_MESSENGER_PAGE_ACCESS_TOKEN` | FB | Facebook page access token |
| `ECO_MESSENGER_APP_SECRET` | FB | Facebook app secret |

## Features

- HMAC signature verification per channel
- Redis-backed conversation sessions with configurable TTL
- Shared message normalizer (unified NormalizedMessage format)
- Typing indicators / sender actions before reply
- Graceful shutdown with connection cleanup
- Structured JSON logging (pino)
- Health + metrics endpoints per adapter
- Push message fallback (LINE) when reply token expires
- Echo message filtering (Messenger)
- Dual mode polling/webhook (Telegram)