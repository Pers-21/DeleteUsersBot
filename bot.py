import asyncio
from aiogram import Dispatcher,Bot,Router
from aiogram.types import Message
from config import token
from aiogram.filters import Command,CommandStart
from commands_buttons.buttons import button
from handlers.delete_users import telethon_client
from handlers import delete_users,schedule_handlers
from handlers.schedule_handlers import scheduler,restore_scheduled_jobs
from database.dp import init_db



bot = Bot(token=token)
dp = Dispatcher()
router = Router()   


dp.include_router(delete_users.router)
dp.include_router(schedule_handlers.router)


@dp.message(CommandStart())
async def start(message:Message):
    await message.answer("Добро пожаловать!")

@dp.message(Command("delete"))
async def delete(message:Message):
    await message.answer("Когда хотите удалить?", reply_markup=button())




async def main():
   await init_db()
   await telethon_client.start()  
   scheduler.start()
   await restore_scheduled_jobs()
   await dp.start_polling(bot)
   await asyncio.Event().wait()
  

if __name__ == "__main__":
    asyncio.run(main())