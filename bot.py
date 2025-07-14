import asyncio

from aiogram import Bot, Dispatcher, html, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from loguru import logger

from config import CONFIG, configure_loguru
from item_worker.base import get_normal_items
from item_worker.float import find_items as float_search_items
from item_worker.stickers import find_items as sticker_search_items

search_status = False

SENDED_ITEMS = set()


def get_start_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="▶️ Стикеры"), KeyboardButton(text="▶️ Флоат"))
    builder.add(KeyboardButton(text="⏹️ Стоп"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


dp = Dispatcher()
bot = Bot(
    token=CONFIG.bot.token, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)


async def start_action(message: types.Message, type: str):
    count = 0
    func = {"sticker": sticker_search_items, "float": float_search_items}[type]

    await message.answer("🟩 Поиск...")

    global search_status
    search_status = True

    try:
        while search_status:
            count += 1
            logger.info(f"Search items, repeat: {count}")
            item_names = get_normal_items()
            tasks = []

            for item_name in item_names:
                if not search_status:
                    break

                task = asyncio.create_task(process_item(func, item_name, message))
                tasks.append(task)

                await asyncio.sleep(CONFIG.sleep.task_sleep)

            await asyncio.gather(*tasks)
            await asyncio.sleep(CONFIG.sleep.task_sleep)

    except asyncio.CancelledError:
        pass


async def process_item(func, item_name, message):
    async for item_id, msg in func(item_name):
        logger.info(f"Find {item_id}, set {SENDED_ITEMS}")
        if item_id in SENDED_ITEMS:
            continue
        SENDED_ITEMS.add(item_id)
        await message.answer(msg)


@dp.message(lambda message: message.text == "▶️ Стикеры")
async def sticker_search(message: types.Message):
    logger.info("start sticker search")
    await start_action(message, "sticker")


@dp.message(lambda message: message.text == "▶️ Флоат")
async def float_search(message: types.Message):
    logger.info("start float search")
    await start_action(message, "float")


@dp.message(lambda message: message.text == "⏹️ Стоп")
async def stop_action(message: types.Message):
    global search_status
    search_status = False
    await message.answer("Останавливаю процесс")


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(
        f"Hello, {html.bold(message.from_user.full_name)}!",
        reply_markup=get_start_keyboard(),
    )


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    configure_loguru(logger)
    asyncio.run(main())
