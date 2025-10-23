import os
import logging
from flask import Flask, request, jsonify
from telegram import Update, InputMediaPhoto, PaidMediaInfo
from telegram.ext import Application, ContextTypes, MessageHandler, filters

# =============================
# CONFIG FROM ENV (RENDER)
# =============================
BOT_TOKEN = os.getenv("BOT_TOKEN")
FULL_IMAGE_PATH = os.getenv("FULL_IMAGE_PATH", "a7x9p2q1z.jpg")
STARS_AMOUNT = int(os.getenv("STARS_AMOUNT", "499"))
PAYLOAD = os.getenv("PAYLOAD", "unlock_image")
TRIGGER_PHRASE = os.getenv("TRIGGER_PHRASE", "send nudes").strip().lower()
CAPTION = os.getenv("CAPTION", "here you go")

# =============================
# VALIDATE BOT_TOKEN
# =============================
if not BOT_TOKEN or not BOT_TOKEN.strip():
    raise RuntimeError("BOT_TOKEN is missing! Set it in Render → Environment Variables.")

# =============================
# GLOBALS
# =============================
business_connection_id = None
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================
# Flask + Telegram App
# =============================
app = Flask(__name__)
application = Application.builder().token(BOT_TOKEN).build()

# =============================
# BOT HANDLERS
# =============================
async def handle_business_connection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle business connection updates (connect/disconnect)"""
    global business_connection_id
    conn = update.business_connection
    if conn and conn.is_enabled:
        business_connection_id = conn.id
        logger.info(f"Business connected: {conn.id} | can_reply={conn.can_reply}")
    else:
        business_connection_id = None
        logger.warning("Business connection disabled or revoked")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming DMs to your personal account"""
    global business_connection_id
    if not business_connection_id or not update.message:
        return

    text = update.message.text or ""
    if TRIGGER_PHRASE not in text.lower():
        return

    if not os.path.exists(FULL_IMAGE_PATH):
        logger.error(f"Image not found: {FULL_IMAGE_PATH}")
        return

    try:
        with open(FULL_IMAGE_PATH, 'rb') as photo_file:
            paid_media = PaidMediaInfo(
                media=InputMediaPhoto(photo_file, caption=CAPTION),
                star_count=STARS_AMOUNT,
                payload=PAYLOAD
            )
            await context.bot.send_photo(
                chat_id=update.message.chat_id,
                photo=photo_file,
                caption=CAPTION,
                paid_media=paid_media,
                business_connection_id=business_connection_id
            )
        logger.info(f"Sent paid photo to {update.message.chat_id}")
    except Exception as e:
        logger.error(f"Send failed: {e}")

async def handle_pre_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Approve Star payments"""
    query = update.pre_checkout_query
    if query.invoice_payload == PAYLOAD:
        await query.answer(ok=True)
    else:
        await query.answer(ok=False, error_message="Invalid payload")

# =============================
# REGISTER HANDLERS
# =============================
# Business connection updates
application.add_handler(MessageHandler(filters.UpdateType.BUSINESS_CONNECTION, handle_business_connection))

# Text messages (in your DMs)
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Pre-checkout queries (payment approval)
application.add_handler(MessageHandler(filters.PRECHECKOUT_QUERY, handle_pre_checkout))

# =============================
# WEBHOOK ENDPOINT
# =============================
@app.route('/webhook', methods=['POST'])
async def webhook():
    try:
        json_data = request.get_json(force=True)
        update = Update.de_json(json_data, application.bot)
        await application.process_update(update)
        return jsonify(success=True)
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify(error=str(e)), 500

@app.route('/')
def home():
    return "<h1>Paid DM Bot Running</h1>Webhook: <code>/webhook</code>"

# =============================
# START SERVER
# =============================
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
