from aiogram.fsm.state import State, StatesGroup

class UserInfo(StatesGroup):
    weight = State()
    height = State()
    age = State()
    activity = State()
    city = State()

class FoodInfo(StatesGroup):
    product_name = State()