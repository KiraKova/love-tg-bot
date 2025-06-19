
import os
import json
import asyncio
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import Router
from dotenv import load_dotenv
from datetime import datetime, timedelta
from aiohttp import web

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 683073014
TARGET_USER_ID = 1175918883  # девушке

ALLOWED_USERS = [OWNER_ID, TARGET_USER_ID]

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

DATA_FILE = "data.json"
HISTORY_FILE = "history.json"
if not os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "w") as f:
        json.dump([], f)

if not os.path.exists(DATA_FILE):
    initial_tasks = [
        {"name": "Завтрак в кровать", "price": 25},
        {"name": "Прогулка", "price": 15},
        {"name": "Купи вкусняшки", "price": 20},
        {"name": "Массаж", "price": 30},
        {"name": "Посмотреть фильм вместе", "price": 10}
    ]
    with open(DATA_FILE, "w") as f:
        json.dump({"balance": 0, "tasks": initial_tasks}, f)

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_history():
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def build_main_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="💰 Добавить поцелуев", callback_data="add_kiss")
    kb.button(text="📝 Добавить задание", callback_data="add_task")
    kb.button(text="📋 Выбрать задание", callback_data="select_task")
    kb.button(text="📊 Просмотр баланса", callback_data="show_balance")
    return kb.adjust(1).as_markup()



def build_task_menu(tasks):
    kb = InlineKeyboardBuilder()
    for idx, task in enumerate(tasks):
        kb.button(text=f"{task['name']} ({task['price']}💋)", callback_data=f"task_{idx}")
        kb.button(text=f"❌ Удалить: {task['name']}", callback_data=f"delete_{idx}")
    kb.button(text="⬅️ Назад", callback_data="go_back")
    return kb.adjust(1).as_markup()



compliments = [
    "Ты — самое прекрасное, что у меня есть 💛",
    "Надеюсь, у тебя сегодня хорошее настроение ☀️",
    "Я всегда рядом, даже если молчу",
    "Ты умеешь делать мой день лучше просто своим присутствием",
    "Я в тебя верю. Всегда.",
    "Ты заслуживаешь самого тёплого и доброго в этом мире",
    "Я с нетерпением жду момента, когда смогу тебя обнять",
    "Каждая твоя улыбка — это мой лучший момент дня 😊",
    "Ты делаешь мою жизнь ярче",
    "Спасибо, что ты есть 💕",
    "Никто не сравнится с тобой — ты особенная",
    "Ты не представляешь, как сильно я тобой горжусь",
    "Если бы можно было, я бы тебе сейчас передал миллион обнимашек 🤗",
    "Ты мой источник вдохновения",
    "Просто знай — ты невероятная",
    "Ты — мой личный супергерой в реальной жизни",
    "Мне повезло, что ты рядом",
    "Каждый день с тобой — это подарок 🎁",
    "Пусть сегодня всё сложится так, как ты хочешь 💫",
    "Скучаю. Очень. Всегда.",
    "Ты сильнее, чем думаешь, и прекраснее, чем видишь в зеркале",
    "Ты заслуживаешь заботы, любви и тепла. И я хочу это тебе давать",
    "Ты умеешь делать даже самый серый день тёплым",
    "Ты не просто чудо — ты моё чудо 💗"
]

async def send_compliment(hour):
    while True:
        now = datetime.utcnow() + timedelta(hours=7)  # Красноярск UTC+7
        if now.hour == hour and now.minute == 0:
            compliment = random.choice(compliments)
            try:
                await bot.send_message(TARGET_USER_ID, f"✨ {compliment}")
            except Exception as e:
                print("Ошибка отправки:", e)
            await asyncio.sleep(60)  # чтобы не повторилось в ту же минуту
        await asyncio.sleep(30)

@router.message(F.text == "/start")
async def start_cmd(message: types.Message):
    await message.answer("Добро пожаловать! Выбери действие:", reply_markup=build_main_menu())

@router.callback_query(F.data == "add_kiss")
async def callback_add_kiss(call: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Назад", callback_data="go_back")
    await call.message.edit_text("Введи количество поцелуев для добавления (например: 10)", reply_markup=kb.as_markup())

@router.message(F.text.regexp(r'^\d+$'))
async def handle_kiss_amount(message: types.Message):
    val = int(message.text)
    data = load_data()
    data["balance"] += val
    save_data(data)
    await message.answer(f"Добавлено {val} 💋. Новый баланс: {data['balance']} 💋", reply_markup=build_main_menu())


@router.callback_query(F.data == "add_task")
async def callback_add_task(call: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Назад", callback_data="go_back")
    await call.message.edit_text("Введи новое задание в формате:\nНазвание:цена", reply_markup=kb.as_markup())

@router.message(F.text.contains(":"))
async def save_task(message: types.Message):
    try:
        name, price = message.text.split(":", 1)
        task = {"name": name.strip(), "price": int(price.strip())}
        data = load_data()
        data["tasks"].append(task)
        save_data(data)
        await message.answer(f"Задание '{task['name']}' за {task['price']} 💋 добавлено!", reply_markup=build_main_menu())
    except:
        await message.answer("Ошибка. Используй формат: Название:цена")

@router.callback_query(F.data == "select_task")
async def show_tasks(call: types.CallbackQuery):
    data = load_data()
    await call.message.edit_text("Выбери задание:", reply_markup=build_task_menu(data["tasks"]))

@router.callback_query(F.data == "show_balance")
async def show_balance(call: types.CallbackQuery):
    data = load_data()
    await call.message.edit_text(f"Твой текущий баланс: {data['balance']} 💋", reply_markup=build_main_menu())

@router.callback_query(F.data.startswith("task_"))
async def task_selected(call: types.CallbackQuery):
    task_index = int(call.data.split("_")[1])
    data = load_data()
    task = data["tasks"][task_index]
    if data["balance"] < task["price"]:
        await call.message.answer("Недостаточно поцелуев для этого задания! 💔", reply_markup=build_main_menu())
        return
    data["balance"] -= task["price"]
    save_data(data)
    await call.message.answer(f"Задание '{task['name']}' выбрано! Остаток: {data['balance']} 💋", reply_markup=build_main_menu())
    await bot.send_message(OWNER_ID, f"📥 Поступил заказ: {task['name']} от @{call.from_user.username}")


@router.message(F.text == "/test_compliment")
async def test_compliment(message: types.Message):
    compliment = random.choice(compliments)
    await message.answer(f"✨ {compliment}")



async def handle_ping(request):
    return web.Response(text="I’m alive!")

async def run_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()



@router.callback_query(F.data == "go_back")
async def go_back_menu(call: types.CallbackQuery):
    await call.message.edit_text("Добро пожаловать! Выбери действие:", reply_markup=build_main_menu())



@router.callback_query(F.data.startswith("delete_"))
async def delete_task(call: types.CallbackQuery):
    index = int(call.data.split("_")[1])
    data = load_data()
    deleted = data["tasks"].pop(index)
    save_data(data)
    await call.message.answer(f"❌ Задание «{deleted['name']}» удалено.", reply_markup=build_main_menu())


async def main():
    asyncio.create_task(send_compliment(10))  # 10:00
    asyncio.create_task(send_compliment(14))  # 14:00
    asyncio.create_task(send_compliment(20))  # 20:00
    asyncio.create_task(run_web_server())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
