from aiogram import Bot, Dispatcher, executor, types

# --- SET YOUR BOT TOKEN HERE ---
API_TOKEN = '8355078489:AAEplo9rAQozIOCW1RhYGWzOYliH8_CLG5I'
LOCKED_IMAGE_PATH = 'a7x9p2q1z.jpg'  # Use your uploaded file
UNLOCK_PRICE = 229  # Number of Stars

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# When user sends trigger phrase
@dp.message_handler(lambda message: 'send nudes' in message.text.lower())
async def send_locked_photo(message: types.Message):
    locked_caption = f"Unlock for ⭐ {UNLOCK_PRICE}"
    await message.answer_photo(types.InputFile(LOCKED_IMAGE_PATH), caption=locked_caption)
    prices = [types.LabeledPrice(label='Unlock photo', amount=UNLOCK_PRICE * 100)]  # Prices in cents (Telegram expects *100)
    await bot.send_invoice(
        chat_id=message.chat.id,
        title="Unlock Photo",
        description="Unlock secret photo",
        payload="photo_unlock",   # Custom payload for this sale
        provider_token="STARS",   # For Stars, use "STARS"
        currency="XTR",           # "XTR" is the Telegram Stars currency
        prices=prices,
        need_name=False
    )

@dp.pre_checkout_query_handler(lambda query: True)
async def pre_checkout_query_handler(query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(query.id, ok=True)

@dp.message_handler(content_types=types.ContentType.SUCCESSFUL_PAYMENT)
async def payment_success(message: types.Message):
    await message.answer_photo(photo=open(LOCKED_IMAGE_PATH, 'rb'), caption="Here is your unlocked photo 💋")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
