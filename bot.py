import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F, Router  # Added F and Router
from aiogram.types import InputPaidMediaPhoto, BusinessConnection
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

# Setup logging
logging.basicConfig(level=logging.INFO)

# Env vars
BOT_TOKEN = os.getenv("8355078489:AAEplo9rAQozIOCW1RhYGWzOYliH8_CLG5I")
BUSINESS_CONNECTION_ID = os.getenv("BUSINESS_CONNECTION_ID")  # Set from logs after connecting
WEBHOOK_PATH = "/webhook"  # Endpoint for Telegram updates
WEBAPP_HOST = "0.0.0.0"  # Listen on all interfaces
WEBAPP_PORT = int(os.getenv("PORT", 10000))  # Render sets PORT env var

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Use Router for handlers (recommended in Aiogram 3)
router = Router()
dp.include_router(router)

@router.message(F.text.lower() == "send stuff")  # Case-insensitive exact match via Magic Filter
async def send_paid_content(message):
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

@dp.business_connection()
async def handle_business_connection(connection: BusinessConnection):
    logging.info(f"Business connection: ID={connection.id}, User ID={connection.user.id}, Enabled={connection.is_enabled}")
    # After seeing this log, update BUSINESS_CONNECTION_ID env var on Render and redeploy

async def on_startup(_):
    # Set webhook URL
    webhook_url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}{WEBHOOK_PATH}"
    await bot.set_webhook(webhook_url)
    logging.info(f"Webhook set to {webhook_url}")

async def on_shutdown(_):
    await bot.delete_webhook()

async def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN env var required")
    
    # Create aiohttp app
    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    
    # Add startup/shutdown hooks
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    
    logging.info("Starting Fan Bot Webhook Server (Via Personal Account)...")
    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)

if __name__ == "__main__":
    asyncio.run(main())
