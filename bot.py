import asyncio
import logging
import os
from aiogram import F, Router, Bot, Dispatcher
from aiogram.filters import Command  # Import Command filter for v3
from aiogram.types import InputPaidMediaPhoto, BusinessConnection
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

# Enable debug logging for Aiogram
logging.basicConfig(level=logging.INFO)
logging.getLogger("aiogram").setLevel(logging.DEBUG)  # Logs full updates

# Env vars
BOT_TOKEN = os.getenv("BOT_TOKEN")
BUSINESS_CONNECTION_ID = os.getenv("BUSINESS_CONNECTION_ID")  # Set from logs after connecting
WEBHOOK_PATH = "/webhook"  # Endpoint for Telegram updates
WEBAPP_HOST = "0.0.0.0"  # Listen on all interfaces
WEBAPP_PORT = int(os.getenv("PORT", 10000))  # Render sets PORT env var

# Global bot (initialized in main)
bot = None

# Use Router for handlers (recommended in Aiogram 3)
router = Router()

@router.message(Command("start"))  # Use Command filter for v3 (no kwargs)
async def cmd_start(message):
    global bot
    await message.reply("Welcome! Say 'send stuff' to unlock paid content via my personal account. 💫")

@router.message(F.text.lower() == "send stuff")  # Case-insensitive exact match via Magic Filter
async def send_paid_content(message):
    global bot
    logging.info(f"Trigger matched! Sending paid media to user {message.from_user.id}")
    if not BUSINESS_CONNECTION_ID:
        await message.reply("Business connection not set up. Check Render logs for the ID and update env var.")
        return
    
    # Define the paid media: locked photo (replace URL with your file_id or hosted image URL)
    media = [
        InputPaidMediaPhoto(
            media="https://picsum.photos/400/600"  # Placeholder; use "file_id" or your image URL
        )
    ]
    
    # Send locked media via your personal account (10 Stars to unlock; adjustable)
    await bot.send_paid_media(
        chat_id=message.chat.id,
        business_connection_id=BUSINESS_CONNECTION_ID,  # Routes through personal account
        media=media,
        star_count=10,  # Stars required (1-10,000)
        payload="fan_bot_unlock_001",  # Track purchases
        caption="Unlock this exclusive content! 💫",  # Appears from your personal profile
    )

@router.business_connection()
async def handle_business_connection(connection: BusinessConnection):
    logging.info(f"Business connection: ID={connection.id}, User ID={connection.user.id}, Enabled={connection.is_enabled}")
    # After seeing this log, update BUSINESS_CONNECTION_ID env var on Render and redeploy

# Catch-all for unmatched messages (debug: logs and replies)
@router.message()
async def debug_all_messages(message):
    logging.info(f"Unhandled message from {message.from_user.id}: '{message.text}' (type: {type(message)})")
    await message.reply("Unknown command. Try /start or 'send stuff' for paid content! 🔒")

async def on_startup(app):
    global bot
    # Set webhook URL
    webhook_url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}{WEBHOOK_PATH}"
    await bot.set_webhook(webhook_url)
    logging.info(f"Webhook set to {webhook_url}")

async def on_shutdown(app):
    global bot
    await bot.delete_webhook()
    await bot.session.close()

async def main():
    global bot
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN env var required—set it in Render Dashboard > Environment")
    
    # Initialize bot and dp here, after check
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    
    # Create aiohttp app
    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    
    # Add startup/shutdown hooks
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    
    # Use AppRunner for fully async server (avoids event loop conflicts)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=WEBAPP_HOST, port=WEBAPP_PORT)
    await site.start()
    
    logging.info("Starting Fan Bot Webhook Server (Via Personal Account)...")
    
    # Run forever
    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
