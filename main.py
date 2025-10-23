# --------------------------------------------------------------
# main.py  –  Paid-DM Telegram Bot (Quart + Uvicorn, Python 3.13)
# --------------------------------------------------------------

import os
import logging
import asyncio
from quart import Quart, request, jsonify  # ASGI-compatible Flask

from telegram import Update, InputMediaPhoto, PaidMediaInfo
from telegram.ext import (
    Application,
    ContextTypes,
    BusinessConnectionHandler,
    MessageHandler,
    PreCheckoutQueryHandler,
    filters,
)

# -------------------------- CONFIG --------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
FULL_IMAGE_PATH = os.getenv("FULL_IMAGE_PATH", "a7x9p2q1z.jpg")
STARS_AMOUNT = int(os.getenv("STARS_AMOUNT", "499"))
PAYLOAD = os.getenv("PAYLOAD", "unlock_image")
TRIGGER_PHRASE = os.getenv("TRIGGER_PHRASE", "send nudes").strip().lower()
CAPTION = os.getenv("CAPTION", "here you go")

# ----------------------- VALIDATION -----------------------
if not BOT_TOKEN or not BOT_TOKEN.strip():
    raise RuntimeError("BOT_TOKEN missing – set it in Render → Environment Variables")

# -------------------------- LOGGING ------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s | %(message)s",
)
log = logging.getLogger("paid-dm-bot")

# -------------------------- GLOBALS ------------------------
business_conn_id: str | None = None
application: Application | None = None

# -------------------------- QUART APP ------------------------
# Patch for Quart/Flask-Sansio config key bug (Python 3.13)
from flask.sansio.app import App as SansioApp
if "PROVIDE_AUTOMATIC_OPTIONS" not in SansioApp.default_config:
    SansioApp.default_config["PROVIDE_AUTOMATIC_OPTIONS"] = True

app = Quart(__name__)

# ----------------------- BOT INITIALIZE --------------------
async def init_bot():
    global application
    log.info("INITIALIZING Telegram Application...")
    application = Application.builder().token(BOT_TOKEN).build()
    await application.initialize()  # REQUIRED
    log.info("Telegram Application INITIALIZED – ready for webhooks")

# ----------------------- HANDLERS -------------------------
async def handle_business_connection(update: Update, _: ContextTypes.DEFAULT_TYPE):
    """Triggered when the business connection is established or removed."""
    global business_conn_id
    conn = update.business_connection
    if conn and conn.is_enabled:
        business_conn_id = conn.id
        log.info("BUSINESS CONNECTED | id=%s can_reply=%s", conn.id, conn.can_reply)
    else:
        business_conn_id = None
        log.warning("BUSINESS DISCONNECTED")

async def handle_message(update: Update, _: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages and send paid media if trigger phrase is detected."""
    global business_conn_id
    if not business_conn_id:
        log.warning("NO BUSINESS CONNECTION – ignoring message")
        return

    if not update.message or not update.message.text:
        log.debug("NON-TEXT message ignored")
        return

    text = update.message.text.strip()
    chat_id = update.message.chat_id
    log.info("INCOMING | chat_id=%s text=%r", chat_id, text)

    if TRIGGER_PHRASE not in text.lower():
        log.debug("Trigger phrase not found in text")
        return

    if not os.path.isfile(FULL_IMAGE_PATH):
        log.error("IMAGE NOT FOUND | path=%s", FULL_IMAGE_PATH)
        return

    try:
        with open(FULL_IMAGE_PATH, "rb") as photo:
            paid_media = PaidMediaInfo(
                media=InputMediaPhoto(photo, caption=CAPTION),
                star_count=STARS_AMOUNT,
                payload=PAYLOAD,
            )

            # Correct Telegram Stars API call
            await application.bot.send_paid_media(
                business_connection_id=business_conn_id,
                paid_media=[paid_media],
            )

        log.info("PAID PHOTO SENT | chat_id=%s", chat_id)

    except Exception as exc:
        log.exception("SEND FAILED | chat_id=%s | %s", chat_id, exc)

async def handle_pre_checkout(update: Update, _: ContextTypes.DEFAULT_TYPE):
    """Confirm payment when Telegram sends a pre-checkout query."""
    query = update.pre_checkout_query
    log.info("PRE-CHECKOUT | payload=%s", query.invoice_payload)
    if query.invoice_payload == PAYLOAD:
        await query.answer(ok=True)
        log.info("PAYMENT APPROVED")
    else:
        await query.answer(ok=False, error_message="Invalid payload")
        log.warning("PAYMENT REJECTED")

# --------------------- REGISTER HANDLERS ------------------
def register_handlers():
    application.add_handler(BusinessConnectionHandler(handle_business_connection))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(PreCheckoutQueryHandler(handle_pre_checkout))

# -------------------------- WEBHOOK ROUTE ------------------
@app.route("/webhook", methods=["POST"])
async def webhook():
    """Receive Telegram updates via webhook."""
    try:
        data = await request.get_json(force=True)
        upd = Update.de_json(data, application.bot)
        await application.process_update(upd)
        return jsonify(success=True)
    except Exception as exc:
        log.exception("WEBHOOK ERROR | %s", exc)
        return jsonify(error=str(exc)), 500

@app.route("/")
async def home():
    return "<h1>Paid-DM Bot LIVE ✅</h1><p>Webhook active at <code>/webhook</code></p>"

# --------------------------- START ------------------------
async def main():
    await init_bot()
    register_handlers()
    log.info("Bot READY – Webhook active at /webhook")

    # Run Quart with uvicorn (ASGI)
    import uvicorn
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 10000)),
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
