/**
 * IndestructibleEco Telegram Bot Adapter
 *
 * Production-grade adapter for Telegram Bot API via Telegraf.
 * Uses shared normalizer for message parsing, shared router for
 * AI backend routing with Redis session management.
 *
 * Features:
 * - Dual mode: polling (dev) / webhook (prod)
 * - Chat action indicators (typing...)
 * - Shared normalizer + router integration
 * - Structured JSON logging
 * - Graceful shutdown
 * - Health command + metrics
 *
 * URI: indestructibleeco://platforms/im-integration/telegram
 */

import { Telegraf, Context } from "telegraf";
import express from "express";
import pino from "pino";
import { normalizeTelegram, type NormalizedMessage } from "../../shared/normalizer";
import { MessageRouter } from "../../shared/router";

// ─── Configuration ───────────────────────────────────────────────────

const BOT_TOKEN = process.env.ECO_TELEGRAM_BOT_TOKEN || "";
const WEBHOOK_URL = process.env.ECO_TELEGRAM_WEBHOOK_URL || "";
const WEBHOOK_PORT = parseInt(process.env.ECO_TELEGRAM_WEBHOOK_PORT || "3001", 10);
const HEALTH_PORT = parseInt(process.env.ECO_TELEGRAM_HEALTH_PORT || "3011", 10);
const MODE = process.env.ECO_TELEGRAM_MODE || "polling";

const logger = pino({
  level: process.env.ECO_LOG_LEVEL || "info",
  name: "eco-telegram-adapter",
});

if (!BOT_TOKEN) {
  logger.fatal({ msg: "ECO_TELEGRAM_BOT_TOKEN is required" });
  process.exit(1);
}

const messageRouter = new MessageRouter(
  process.env.ECO_REDIS_URL || "redis://localhost:6379"
);

// ─── Metrics ─────────────────────────────────────────────────────────

const metrics = {
  messages_received: 0,
  messages_sent: 0,
  commands_received: 0,
  api_errors: 0,
  started_at: new Date().toISOString(),
};

// ─── Bot Setup ───────────────────────────────────────────────────────

const bot = new Telegraf(BOT_TOKEN);

// ─── Reply Helper ────────────────────────────────────────────────────

export async function sendTelegramReply(
  ctx: Context,
  text: string
): Promise<boolean> {
  try {
    await ctx.reply(text, { parse_mode: "Markdown" });
    metrics.messages_sent++;
    return true;
  } catch (err) {
    // Fallback without markdown if parse fails
    try {
      await ctx.reply(text);
      metrics.messages_sent++;
      return true;
    } catch (err2) {
      logger.error({
        msg: "Telegram send failed",
        error: (err2 as Error).message,
      });
      metrics.api_errors++;
      return false;
    }
  }
}

// ─── Command Handlers ────────────────────────────────────────────────

bot.command("start", async (ctx) => {
  metrics.commands_received++;
  await ctx.reply(
    "🤖 *IndestructibleEco AI Bot*\n\n" +
      "Send any message to start a conversation with AI.\n\n" +
      "Commands:\n" +
      "/start — Show this message\n" +
      "/health — Check bot status\n" +
      "/reset — Reset conversation",
    { parse_mode: "Markdown" }
  );
});

bot.command("health", async (ctx) => {
  metrics.commands_received++;
  await ctx.reply(
    JSON.stringify(
      {
        status: "healthy",
        channel: "telegram",
        mode: MODE,
        messages_processed: metrics.messages_received,
        uptime_since: metrics.started_at,
      },
      null,
      2
    )
  );
});

bot.command("reset", async (ctx) => {
  metrics.commands_received++;
  await ctx.reply("🔄 Conversation reset. Send a new message to start fresh.");
});

// ─── Message Handler ─────────────────────────────────────────────────

bot.on("message", async (ctx) => {
  const msg = ctx.message;
  if (!msg || !("text" in msg)) return;
  if (msg.text.startsWith("/")) return; // Skip commands

  metrics.messages_received++;

  // Build raw payload for shared normalizer
  const rawPayload = {
    message: {
      message_id: msg.message_id,
      from: msg.from,
      chat: msg.chat,
      text: msg.text,
      date: msg.date,
      reply_to_message: (msg as any).reply_to_message || null,
    },
  };

  const normalized: NormalizedMessage = normalizeTelegram(rawPayload);

  logger.info({
    msg: "Processing Telegram message",
    userId: normalized.userId,
    chatId: normalized.metadata?.chatId,
    messageId: normalized.id,
    uri: normalized.uri,
  });

  // Send typing indicator
  try {
    await ctx.sendChatAction("typing");
  } catch {
    // Non-critical
  }

  // Route through shared router
  try {
    const response = await messageRouter.route(normalized);
    await sendTelegramReply(ctx, response.text);

    logger.info({
      msg: "Telegram reply sent",
      userId: normalized.userId,
      conversationId: response.metadata?.conversationId,
    });
  } catch (err) {
    logger.error({
      msg: "Telegram processing failed",
      userId: normalized.userId,
      error: (err as Error).message,
    });
    await ctx.reply("Sorry, I encountered an error. Please try again.");
    metrics.api_errors++;
  }
});

// ─── Health Server (separate from bot) ───────────────────────────────

const healthApp = express();

healthApp.get("/health", (_req, res) =>
  res.json({
    status: "healthy",
    channel: "telegram",
    version: "2.0.0",
    mode: MODE,
    api: process.env.ECO_API_URL || "http://localhost:3000",
    uri: "indestructibleeco://platforms/im-integration/telegram/health",
    timestamp: new Date().toISOString(),
  })
);

healthApp.get("/metrics", (_req, res) =>
  res.json({
    ...metrics,
    uri: "indestructibleeco://platforms/im-integration/telegram/metrics",
    timestamp: new Date().toISOString(),
  })
);

// ─── Launch ──────────────────────────────────────────────────────────

let healthServer: ReturnType<typeof healthApp.listen>;

if (MODE === "webhook" && WEBHOOK_URL) {
  bot.launch({ webhook: { domain: WEBHOOK_URL, port: WEBHOOK_PORT } });
  logger.info({
    msg: "Telegram bot started in webhook mode",
    webhookUrl: WEBHOOK_URL,
    port: WEBHOOK_PORT,
  });
} else {
  bot.launch();
  logger.info({ msg: "Telegram bot started in polling mode" });
}

healthServer = healthApp.listen(HEALTH_PORT, () => {
  logger.info({
    msg: "Telegram health server started",
    port: HEALTH_PORT,
    uri: "indestructibleeco://platforms/im-integration/telegram",
  });
});

// ─── Graceful Shutdown ───────────────────────────────────────────────

function shutdown(signal: string) {
  logger.info({ msg: `Received ${signal}, shutting down Telegram adapter` });
  bot.stop(signal);
  healthServer?.close(() => {
    messageRouter.destroy().then(() => process.exit(0));
  });
  setTimeout(() => process.exit(1), 10000);
}

process.once("SIGINT", () => shutdown("SIGINT"));
process.once("SIGTERM", () => shutdown("SIGTERM"));

export { bot, healthApp };