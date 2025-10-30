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
)
from aiogram.enums import ChatType

app = FastAPI()

bot: Bot = None
dp: Dispatcher = None

# ==============================================================
# ====  CUSTOMISE THESE  ========================================
# ==============================================================

IMAGE_URL = "https://graph.org/file/83300c88a9199a6459eb5-9f9ba39b172f8985ef.jpg"   # CHANGE
STAR_PRICE = 139                                        # CHANGE
TRIGGER_WORDS = [
    "naked", "nude", "see you", "photo", "pic", "nudes",
    "tits", "ass", "pussy"
]                                                       # CHANGE

# ==============================================================

@asynccontextmanager
async def lifespan(_: FastAPI) -> Any:
    global bot, dp
    bot = Bot(token=os.environ["BOT_TOKEN"])
    dp = Dispatcher()

    @dp.message(F.chat.type == "private")
    async def private_dm(message):
        if message.from_user.is_bot:
            return

        txt = (message.text or "").lower()
        if any(word in txt for word in TRIGGER_WORDS):
            name = message.from_user.username or message.from_user.first_name or "cutie"
            caption = f"Hope you enjoy that view {name}"

            media = [InputPaidMediaPhoto(media=URLInputFile(url=IMAGE_URL))]

            try:
                await bot.send_paid_media(
                    chat_id=message.chat.id,
                    media=media,
                    star_count=STAR_PRICE,
                    caption=caption,
                    payload=f"sale_{message.from_user.id}"
                )
                print(f"SENT PAID MEDIA → {name} (ID:{message.from_user.id})")
            except Exception as e:
                print(f"ERROR sending paid media: {e}")

    @dp.update(F.paid_media_purchased)
    async def sale(update: Update):
        paid: PaidMediaPurchased = update.paid_media_purchased
        print(f"SALE! User: {paid.from_user.id} | Payload: {paid.paid_media_payload}")

    @dp.message()
    async def debug(msg):
        print(f"IN: '{msg.text}' | Chat:{msg.chat.id} | Type:{msg.chat.type}")

    webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/webhook"
    await bot.set_webhook(url=webhook_url, drop_pending_updates=True)
    print(f"Webhook → {webhook_url}")

    yield

    await dp.shutdown()
    await bot.session.close()

app.router.lifespan_context = lifespan

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update(**data)
    await dp.feed_update(bot, update)
    return JSONResponse({"ok": True})

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
