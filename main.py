import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Update,
    URLInputFile,
    InputPaidMediaPhoto,
    PaidMediaPurchased,
    BusinessMessage,
)

app = FastAPI()
bot: Bot = None
dp = Dispatcher()

# ==============================================================
# CUSTOMIZE HERE
# ==============================================================
IMAGE_URL = "https://graph.org/file/7ce66e7aaa31c083758ba-fb872221fd56cfd66c.jpg"   # Direct public link
STAR_PRICE = 139                                        # Stars to unlock
TRIGGER_WORDS = [
    "naked", "nude", "photo", "pic", "nudes", "tits", "ass", "pussy", "see you"
]                                                       # Add/remove words
# ==============================================================

@asynccontextmanager
async def lifespan(_: FastAPI) -> Any:
    global bot
    bot = Bot(token=os.environ["BOT_TOKEN"])
    dp = Dispatcher()

    # BUSINESS DM HANDLER (DMs to your personal account)
    @dp.business_message()
    async def handle_business_dm(message: BusinessMessage):
        user = message.from_user
        if user.is_bot:
            return

        text = (message.text or "").lower()
        if any(word in text for word in TRIGGER_WORDS):
            name = user.username or user.first_name or "cutie"
            caption = f"Hope you enjoy that view {name}"

            media = [InputPaidMediaPhoto(media=URLInputFile(IMAGE_URL))]

            try:
                await bot.send_paid_media(
                    chat_id=message.chat.id,
                    business_connection_id=message.business_connection_id,
                    star_count=STAR_PRICE,
                    caption=caption,
                    payload=f"sale_{user.id}",
                    media=media
                )
                print(f"SENT PAID MEDIA to {name} (ID: {user.id})")
            except Exception as e:
                print(f"ERROR: {e}")

    # SALE LOG
    @dp.update(F.paid_media_purchased)
    async def on_sale(update: Update):
        paid: PaidMediaPurchased = update.paid_media_purchased
        print(f"SALE! Stars: {paid.stars} | User: {paid.user.id} | Payload: {paid.payload}")

    # DEBUG: See all incoming DMs
    @dp.business_message()
    async def debug(message: BusinessMessage):
        print(f"DM: '{message.text}' | User: {message.from_user.id} | Conn: {message.business_connection_id}")

    # SET WEBHOOK
    webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/webhook"
    await bot.set_webhook(url=webhook_url, drop_pending_updates=True)
    print(f"WEBHOOK SET: {webhook_url}")

    yield
    await dp.shutdown()
    await bot.session.close()

app.router.lifespan_context = lifespan

# WEBHOOK ENDPOINT
@app.post("/webhook")
async def webhook(request: Request):
    update = Update(**(await request.json()))
    await dp.feed_update(bot, update)
    return JSONResponse({"ok": True})

# LOCAL DEV
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), reload=False)
