from aiogram import Bot, Dispatcher, executor, types

API_TOKEN = 'YOUR_BOT_API_TOKEN'
PROVIDER_TOKEN = 'YOUR_PROVIDER_TOKEN'
LOCKED_IMAGE_PATH = 'photo_2025-10-30_05-04-19.jpg'  # Use your uploaded file
UNLOCK_PRICE = 229  # Number of Stars

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# When user sends trigger phrase
@dp.message_handler(lambda message: 'send nudes' in message.text.lower())
async def send_locked_photo(message: types.Message):
    locked_caption = f"Unlock for ⭐ {UNLOCK_PRICE}"
    # Send "locked" image with unlock caption
    await message.answer_photo(types.InputFile(LOCKED_IMAGE_PATH), caption=locked_caption)

    # Follow with unlock invoice for Stars
    prices = [types.LabeledPrice(label='Unlock photo', amount=UNLOCK_PRICE * 100)]  # Telegram price is in cents
    await bot.send_invoice(
        chat_id=message.chat.id,
        title="Unlock Photo",
        description="Unlock secret photo",
        payload="photo_unlock",
        provider_token=PROVIDER_TOKEN,
        currency="XTR",
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
