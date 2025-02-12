from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states import UserInfo, FoodInfo
import aiohttp
from utils import calculate_water_norm, calculate_calorie_norm, get_weather, get_food_info
from config import WEATHER_TOKEN

router = Router()
USERS = {}

# Обработчик команды /start
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await message.reply("Добро пожаловать! Я ваш бот.\nВведите /help для списка команд.")
    await state.clear()

# Обработчик команды /help
@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.reply(
        "Доступные команды:\n"
        "/start - Начало работы\n"
        "/set_profile - Настройка профиля пользователя\n"
        """/log_water <количество>:
            - Сохраняет, сколько воды выпито. 
            - Показывает, сколько осталось до выполнения нормы.\n"""
        """/log_food <название продукта> - Подсчет калорийности.\n"""
        """/log_workout <тип тренировки> <время (мин)>:
            - Фиксирует сожжённые калории.
            - Учитывает расход воды на тренировке (дополнительные 200 мл за каждые 30 минут) или более умный учет разных типов тренировок.\n"""
        "/check_progress - Показывает, сколько воды и калорий потреблено, сожжено и сколько осталось до выполнения цели\n"
        "/new_day - Показывает сводку по дню и пересчитывает целевые показатели"
    )


def check_profile(user_id):
    if user_id not in USERS or not all(
        key in USERS[user_id] for key in ["weight", "height", "age", "activity", "city"]
    ):
        return False
    return True


# FSM: диалог с пользователем
@router.message(Command("set_profile"))
async def set_profile(message: Message, state: FSMContext):
    await message.reply("Введите ваш вес (в кг)")
    await state.set_state(UserInfo.weight)

@router.message(UserInfo.weight)
async def process_weight(message: Message, state: FSMContext):
    await state.update_data(weight=message.text)
    try:
        weight = float(message.text)
        if weight <= 0:
            raise ValueError("Вес должен быть больше 0")
        await state.update_data(weight=weight)
        await message.reply("Введите ваш рост (в см):")
        await state.set_state(UserInfo.height)
    except ValueError:
        await message.reply("Некорректный вес. Введите число больше 0")

@router.message(UserInfo.height)
async def process_height(message: Message, state: FSMContext):
    try:
        height = float(message.text)
        if height <= 0:
            raise ValueError("Рост должен быть больше 0")
        await state.update_data(height=height)
        await message.reply("Введите ваш возраст:")
        await state.set_state(UserInfo.age)
    except ValueError:
        await message.reply("Некорректный рост. Введите число больше 0")

@router.message(UserInfo.age)
async def process_age(message: Message, state: FSMContext):
    try:
        age = int(message.text)
        if age <= 0:
            raise ValueError("Возраст должен быть больше 0")
        await state.update_data(age=age)
        await message.reply("Сколько минут активности у вас в день?")
        await state.set_state(UserInfo.activity)
    except ValueError:
        await message.reply("Некорректный возраст. Введите целое число больше 0")

@router.message(UserInfo.activity)
async def process_activity(message: Message, state: FSMContext):
    try:
        activity = int(message.text)
        if activity < 0:
            raise ValueError("Активность не может быть отрицательной")
        await state.update_data(activity=activity)
        await message.reply("В каком городе вы находитесь? (на русском)")
        await state.set_state(UserInfo.city)
    except ValueError:
        await message.reply("Некорректное значение. Введите целое число больше 0")

@router.message(UserInfo.city)
async def process_city(message: Message, state: FSMContext):
    city = message.text
    await state.update_data(city=city)
    user_data = await state.get_data()
    USERS[message.from_user.id] = user_data
    try:
        USERS[message.from_user.id]['weather'] = await get_weather(WEATHER_TOKEN, city)
        weather = USERS[message.from_user.id]['weather']
    except:
        USERS[message.from_user.id]['weather'] = None
        weather = 'Погода не найдена' 
    USERS[message.from_user.id]['water_remains'] = calculate_water_norm(user_data)
    USERS[message.from_user.id]['calories_remains'] = calculate_calorie_norm(user_data)
    USERS[message.from_user.id]["logged_water"] = 0
    USERS[message.from_user.id]["logged_calories"] = 0
    USERS[message.from_user.id]["calories_balance"] = 0
    await message.reply(
        f"Профиль успешно настроен!\n"
        f"Ваши данные:\n"
        f"- Вес: {user_data['weight']} кг\n"
        f"- Рост: {user_data['height']} см\n"
        f"- Возраст: {user_data['age']} лет\n"
        f"- Активность: {user_data['activity']} минут в день\n"
        f"- Город: {user_data['city']}\n"
        f"- Погода: {weather} C.\n"
        f"- Норма воды: {USERS[message.from_user.id]['water_remains']} мл.\n"
        f"- Норма калорий: {USERS[message.from_user.id]['calories_remains']} ккал."
    )

    await state.clear()


# Логирование воды
@router.message(Command("log_water"))
async def log_water(message: Message):
    user_id = message.from_user.id
    if not check_profile(user_id):
        await message.reply("Вы не зарегистрированы. Используйте /set_profile для настройки профиля")
        return
    try:
        water_amount = int(message.text.split(maxsplit=1)[1]) \
        if len(message.text.split()) > 1 else None
        if not water_amount:
            await message.reply("Используйте команду так: /log_water <количество> в мл.")
            return
        USERS[user_id]["logged_water"] = USERS[user_id].get("logged_water", 0) + water_amount
        USERS[user_id]['water_remains'] = USERS[user_id].get("water_remains", 0) - water_amount
        await message.reply(f"Записано: {water_amount} мл воды.")
        if USERS[user_id]['water_remains'] > 0:
            await message.reply(f"До выполнения нормы: {USERS[user_id]['water_remains']} мл воды")
        else:
            await message.reply(f"Норма воды выпита")
    except (ValueError, IndexError, TypeError):
        await message.reply("Используйте команду так: /log_water <количество> в мл (целое число)")

@router.message(Command("new_day"))
async def new_day(message: Message):
    user_id = message.from_user.id
    if not check_profile(user_id):
        await message.reply("Вы не зарегистрированы. Используйте /set_profile для настройки профиля")
        return
    await message.reply(f"За день выпито: {USERS[user_id]["logged_water"]} мл воды.")
    if USERS[user_id]['water_remains'] > 0:
        await message.reply(f"До выполнения нормы: {USERS[user_id]['water_remains']} мл воды")
    else:
        await message.reply(f"Норма воды выпита")
    
    await message.reply(f"За день съедено: {USERS[user_id]["logged_calories"]} ккал")
    if USERS[user_id]['calories_remains'] > 0:
        await message.reply(f"До выполнения нормы: {USERS[user_id]['calories_remains']:.2f} ккал.")
    else:
        calories_remains = -1 * USERS[user_id]['calories_remains']
        await message.reply(f"Норма ккал превышена на {calories_remains:.2f}")
    USERS[user_id]["logged_water"] = 0
    USERS[user_id]["logged_calories"] = 0
    city = USERS[user_id]['city']
    try:
        USERS[message.from_user.id]['weather'] = await get_weather(WEATHER_TOKEN, city)
    except:
        USERS[message.from_user.id]['weather'] = None
    USERS[user_id]['water_remains'] = calculate_water_norm(USERS[user_id])
    USERS[user_id]['calories_remains'] = calculate_calorie_norm(USERS[user_id])
    await message.reply(f"Новый день начат\n"
                        f"- Норма воды: {USERS[message.from_user.id]['water_remains']} мл.\n"
                        f"- Норма калорий: {USERS[message.from_user.id]['calories_remains']} ккал.")


@router.message(Command("check_progress"))
async def check_progress(message: Message):
    user_id = message.from_user.id
    if not check_profile(user_id):
        await message.reply("Вы не зарегистрированы. Используйте /set_profile для настройки профиля")
        return
    await message.reply(f"За день выпито: {USERS[user_id]["logged_water"]} мл воды.")
    if USERS[user_id]['water_remains'] > 0:
        await message.reply(f"До выполнения нормы: {USERS[user_id]['water_remains']} мл воды")
    else:
        await message.reply(f"Норма воды выпита")
    
    await message.reply(f"За день съедено: {USERS[user_id]["logged_calories"]} ккал")
    if USERS[user_id]['calories_remains'] > 0:
        await message.reply(f"До выполнения нормы: {USERS[user_id]['calories_remains']:.2f} ккал.")
    else:
        calories_remains = -1 * USERS[user_id]['calories_remains']
        await message.reply(f"Норма ккал превышена на {calories_remains:.2f}")
    await message.reply(f"За день сожжено: {USERS[user_id]["burned_calories"]} ккал")
    await message.reply(f"Баланс калорий: {USERS[user_id]["calories_balance"]} ккал")


@router.message(Command("log_food"))
async def log_food(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if not check_profile(user_id):
        await message.reply("Вы не зарегистрированы. Используйте /set_profile для настройки профиля")
        return

    product_name = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
    if not product_name:
        await message.reply("Укажите название продукта. Пример: /log_food банан")
        return

    food_info = await get_food_info(product_name)
    if not food_info:
        await message.reply("Продукт не найден. Попробуйте ещё раз.")
        return

    await state.update_data(food_info=food_info)
    await message.reply(f"В {food_info['name']} — {food_info['calories']} ккал на 100 г. Сколько грамм вы съели?")
    await state.set_state(FoodInfo.product_name)

@router.message(FoodInfo.product_name)
async def process_grams(message: Message, state: FSMContext):
    try:
        grams = float(message.text)
        if grams <= 0:
            raise ValueError("Количество грамм должно быть больше 0")
        user_data = await state.get_data()
        food_info = user_data['food_info']

        calories = (food_info['calories'] * grams) / 100
        user_id = message.from_user.id
        USERS[user_id]["logged_calories"] = USERS[user_id].get("logged_calories", 0) + calories
        USERS[user_id]['calories_remains'] = USERS[user_id].get("calories_remains", 0) - calories
        USERS[user_id]['calories_balance'] = USERS[user_id].get("calories_balance", 0) + calories
        await message.reply(f"Записано: {calories:.1f} ккал.")

        if USERS[user_id]['calories_remains'] > 0:
            await message.reply(f"До выполнения нормы: {USERS[user_id]['calories_remains']:.2f} ккал.")
        else:
            calories_remains = -1 * USERS[user_id]['calories_remains']
            await message.reply(f"Норма ккал превышена на {calories_remains:.2f}")
        
        await state.clear()
    except (ValueError, TypeError):
        await message.reply("Некорректное значение. Введите число больше 0")

@router.message(Command("log_workout"))
async def log_workout(message: Message):
    user_id = message.from_user.id
    if not check_profile(user_id):
        await message.reply("Вы не зарегистрированы. Используйте /set_profile для настройки профиля")
        return
    try:
        workout_type = message.text.split(maxsplit=2)[1] if len(message.text.split()) > 1 else None
        duration = int(message.text.split(maxsplit=2)[2]) if len(message.text.split()) > 2 else None
        burned_calories = duration * len(workout_type)
        USERS[user_id]["burned_calories"] = USERS[user_id].get("burned_calories", 0) + burned_calories
        if USERS[user_id]["calories_balance"] - burned_calories > 0:
            USERS[user_id]["calories_balance"] = USERS[user_id]["calories_balance"] - burned_calories
        else:
            USERS[user_id]["calories_balance"] = 0
        
        await message.reply(f"Записано: {burned_calories} ккал сожжено")
        additional_water = (duration // 30) * 200
        await message.reply(f"Дополнительно: выпейте {additional_water} мл воды (они уже учтены)")
        USERS[user_id]["logged_water"] = USERS[user_id].get("logged_water", 0) + additional_water
        USERS[user_id]['water_remains'] = USERS[user_id].get("water_remains", 0) - additional_water
    except (ValueError, IndexError, TypeError):
        await message.reply("Используйте команду так: /log_workout <тип тренировки> <время в минутах>")



# Функция для подключения обработчиков
def setup_handlers(dp):
    dp.include_router(router)
