from aiogram.fsm.state import State, StatesGroup


class BookingStates(StatesGroup):
    waiting_for_full_name = State()
    waiting_for_age = State()
    waiting_for_gender = State()