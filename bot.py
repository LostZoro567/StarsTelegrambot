import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.types import InputPaidMediaPhoto, BusinessConnection, PaidMediaPurchased
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

logging.basicConfig(level=logging.INFO)
logging.getLogger("aiogram").setLevel(logging.DEBUG)

# Env vars
BOT_TOKEN = os.getenv("BOT_TOKEN")
BUSINESS_CONNECTION_ID = os.getenv("BUSINESS_CONNECTION_ID", "")  # Optional: "" for direct bot send
IMAGE_FILE_ID = os.getenv("IMAGE_FILE_ID", "AgACAgIAAxkBAAIB...")  # Replace with your real file_id
WEBHOOK_PATH = "/webhook"
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 10000))

router = Router()

@router.message(Command("start"))
async def start_handler(message, bot: Bot):
    await message.reply("Hi! Send 'send stuff' to get exclusive paid content. 💫")

@router.message(F.text.lower() == "send stuff")
async def send_paid_content(message, bot: Bot):
    logging.info(f"Trigger: Sending to user {message.from_user.id}")
    
    media = [InputPaidMediaPhoto(media=IMAGE_FILE_ID)]  # Use file_id for reliability
    
    try:
        await bot.send_paid_media(
            chat_id=message.chat.id,
            media=media,
            star_count=10,  # Adjust 1-10,000
            payload="fan_unlock_001",
            caption="Unlock this fan exclusive! 🔥",
            business_connection_id=BUSINESS_CONNECTION_ID if BUSINESS_CONNECTION_ID else None,  # Optional for personal send
        )
        logging.info(f"Success: Paid media sent to {message.chat.id}")
    except Exception as e:
        logging.error(f"Send failed: {e}")
        await message.reply(f"Error sending: {str(e)}. Check logs.")

@router.message()
async def catch_all(message):
    await message.reply("Try /start or 'send stuff'!")

async def handle_business_connection(connection: BusinessConnection, bot: Bot):
    logging.info(f"Business connected! ID: {connection.id}, User: {connection.user.id}, Enabled: {connection.is_enabled}")
    # Copy ID to env var for personal sending

async def handle_purchase(purchase: PaidMediaPurchased, bot: Bot):
    logging.info(f"Purchase! User {purchase.user_id} paid {purchase.star_count} for {purchase.payload}")
    await bot.send_message(
        purchase.user_id,
        "Thanks for unlocking! More soon? 😘",
        business_connection_id=BUSINESS_CONNECTION_ID if BUSINESS_CONNECTION_ID else None
    )

async def on_startup(app, bot: Bot):
    webhook_url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}{WEBHOOK_PATH}"
    await bot.set_webhook(webhook_url)
    logging.info(f"Webhook: {webhook_url}")

async def on_shutdown(app, bot: Bot):
    await bot.delete_webhook()
    await bot.session.close()

async def main():
    if not BOT_TOKEN:
        raise ValueError("Set BOT_TOKEN in Render env")
    
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    
    # Special handlers (injected with bot)
    dp.business_connection(handle_business_connection, bot=bot)
    dp.paid_media_purchased(handle_purchase, bot=bot)
    
    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    app.on_startup.append(lambda app: on_startup(app, bot))
    app.on_shutdown.append(lambda app: on_shutdown(app, bot))
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=WEBAPP_HOST, port=WEBAPP_PORT)
    await site.start()
    logging.info("Bot live!")
    
    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
