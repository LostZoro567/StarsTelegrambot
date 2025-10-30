import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    InputPaidMediaPhoto,
    URLInputFile,
    BusinessConnection,
    Update,
    PaidMediaPurchased,
)

app = FastAPI()

bot: Bot = None
dp: Dispatcher = None

# ===== CUSTOMIZE HERE =====
IMAGE_URL = "https://i.imgur.com/YOUR_FULL_PHOTO.jpg"  # <- REPLACE with YOUR public image URL
STAR_PRICE = 139  # Stars to unlock
TRIGGER_WORDS = ["naked", "nude", "see you", "photo", "pic", "nudes", "tits", "ass", "pussy"]  # Add more

@asynccontextmanager
async def lifespan(app_: FastAPI) -> Any:
    global bot, dp
    bot = Bot(token=os.environ["BOT_TOKEN"])
    dp = Dispatcher()

    # --- BUSINESS MESSAGE HANDLER ---
    @dp.message(F.business_connection_id)
    async def handle_request(message):
        if message.text and any(word in message.text.lower() for word in TRIGGER_WORDS):
            # Personalize like screenshot
            name = message.from_user.username or message.from_user.first_name or "cutie"
            caption = f"Hope you enjoy that view {name} 💋"

            # Send LOCKED media (Telegram auto-blurs + "Unlock for ★{PRICE}")
            media = [InputPaidMediaPhoto(media=URLInputFile(url=IMAGE_URL))]
            await bot.send_paid_media(
                chat_id=message.chat.id,
                media=media,
                star_count=STAR_PRICE,
                caption=caption,
                payload=f"sale_{message.from_user.id}"
            )
            print(f"Sent paid media to {name}!")

    # --- OPTIONAL: Connection/Sales Logs ---
    @dp.business_connection()
    async def on_connect(conn: BusinessConnection):
        print(f"✅ Business connected: {conn.user.id}")

    @dp.update(F.paid_media_purchased)
    async def on_sale(update: Update):
        paid = update.paid_media_purchased
        print(f"💰 SALE! Stars: {paid.stars} | Payload: {paid.payload}")

    # Set Webhook
    webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/webhook"
    await bot.set_webhook(url=webhook_url, drop_pending_updates=True)
    print(f"🚀 Webhook: {webhook_url}")

    yield

    await dp.shutdown()
    await bot.session.close()

app.router.lifespan_context = lifespan

@app.post("/webhook")
async def webhook(request: Request):
    update_raw = await request.json()
    await dp.feed_update(bot, update_raw)
    return JSONResponse({"ok": True})

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
