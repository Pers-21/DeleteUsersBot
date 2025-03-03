from aiogram.types import ReplyKeyboardMarkup,KeyboardButton,Message
from aiogram import Router

router = Router()

def button():
    keyboar = ReplyKeyboardMarkup(
        keyboard=[
        [KeyboardButton(text="🗑️Удалить пользывателей сейчас")],
        [KeyboardButton(text="⏳Удалить пользывателей через...")],
        [KeyboardButton(text="🚫 Отменить удаление")]

    ],
    resize_keyboard=True
    )
    return keyboar

def schedule_buttons():
    schedule_keybord = ReplyKeyboardMarkup(keyboard =[
        [KeyboardButton(text="🗑️Удалить через 1 мес")],
        [KeyboardButton(text="🗑️Удалить через 3 мес")],
        [KeyboardButton(text="🗑️Удалить через 6 мес")],
        [KeyboardButton(text="🗑️Удалить через 1 год")]
        ],
        resize_keyboard=True
        )
    return schedule_keybord