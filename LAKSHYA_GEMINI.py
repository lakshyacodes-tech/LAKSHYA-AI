# ============================================================
#  LAKSHYA GEMINI TELEGRAM BOT  |  @lakshyaxgod1
# ============================================================
import httpx
import time
import asyncio
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ---------- CONFIG ----------
BOT_TOKEN = "9261501359:AAHChlBWeTzega7sDFU8F_QfOT_c1-2A5L0"
API       = "AQ.Ab8RN6LRthMEy6QOa0t2IDO1ydaw3Ysao3lSUHtR9ul9BwYN-A"
MDL       = "gemini-3.5-flash-lite" 
URL       = f"https://generativelanguage.googleapis.com/v1beta/models/{MDL}:generateContent"

S   = "━" * 40
DEV = "👨‍💻 Developer: @lakshyaxgod1\n📢 Channel: @lakshyaxera"

# ---------- LOGGING ----------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ---------- GLOBAL HTTP CLIENT ----------
http_client = httpx.AsyncClient(http2=True, timeout=30.0)

# ---------- USER HISTORY STORE ----------
user_history: dict[int, list] = {}

# ---------- GEMINI CALL WITH RETRY ----------
async def gemini_call(payload: dict, max_retries: int = 3):
    for attempt in range(max_retries):
        r = await http_client.post(
            URL,
            headers={
                "Content-Type": "application/json",
                "X-goog-api-key": API,
            },
            json=payload,
        )
        if r.status_code in (503, 429, 500):
            wait = 1.5
            logger.warning(f"⚠️ Server {r.status_code} → retry in {wait}s")
            await asyncio.sleep(wait)
            continue
        r.raise_for_status()
        return r.json()
    raise Exception("Gemini API failed after retries ❌")

# ---------- /start ----------
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_history[update.effective_chat.id] = []
    
    text = (
        f"{S}\n"
        f"🤖  *LAKSHYA GEMINI TELEGRAM BOT*\n"
        f"{S}\n"
        f"{DEV}\n"
        f"{S}\n\n"
        f"⚡ *Fast Mode Enabled!* Just type your question.\n"
        f"🧹 /reset — Clear memory\n"
        f"ℹ️ /help — Commands\n"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# ---------- /help ----------
async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        f"{S}\n"
        f"📖 *Available Commands*\n"
        f"{S}\n"
        f"🚀 /start — Restart the bot\n"
        f"🧹 /reset — Clear chat memory\n"
        f"ℹ️ /help  — Show this menu\n"
        f"{S}\n"
        f"{DEV}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# ---------- /reset ----------
async def reset(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_history[update.effective_chat.id] = []
    await update.message.reply_text("🧹 *Chat memory cleared successfully!*", parse_mode="Markdown")

# ---------- MESSAGE HANDLER ----------
async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    question = (update.message.text or "").strip()

    if not question:
        return

    if question.lower() in ("exit", "çık"):
        await update.message.reply_text("👋 Bye!")
        return

    history = user_history.setdefault(chat_id, [])
    history.append({"role": "user", "parts": [{"text": question}]})

    # Thinking message
    msg = await update.message.reply_text("⏳ Thinking...")

    try:
        payload = {
            "contents": history,
            "generationConfig": {
                "maxOutputTokens": 1024,
                "temperature": 0.7,
            }
        }
        data = await gemini_call(payload)
        answer = data["candidates"][0]["content"]["parts"][0]["text"]
        history.append({"role": "model", "parts": [{"text": answer}]})

        chunks = [answer[i:i + 4000] for i in range(0, len(answer), 4000)]
        
        try:
            # Thinking msg ko answer se replace kar dega
            await msg.edit_text(chunks[0])
        except Exception:
            await update.message.reply_text(chunks[0])
            
        for extra in chunks[1:]:
            await update.message.reply_text(extra)

    except httpx.HTTPStatusError as e:
        await msg.edit_text(f"❌ HTTP {e.response.status_code}\n{e.response.text[:100]}")
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")

# ---------- ERROR HANDLER ----------
async def error_handler(update: object, ctx: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {ctx.error}")

# ---------- SHUTDOWN ----------
async def on_shutdown(app):
    await http_client.aclose()

# ---------- MAIN ----------
def main():
    print(S)
    print("🤖  LAKSHYA GEMINI TELEGRAM BOT")
    print(S)
    print(DEV)
    print(S)

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .post_shutdown(on_shutdown)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    print("✅ Bot is polling...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()