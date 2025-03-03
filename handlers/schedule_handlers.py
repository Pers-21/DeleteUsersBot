from aiogram.types import Message
from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telethon.tl.types import ChatBannedRights
from telethon.tl.functions.channels import EditBannedRequest
from handlers.delete_users import telethon_client,get_admins_and_owner
import asyncio
from datetime import datetime, timedelta
from commands_buttons.buttons import schedule_buttons
from database.dp import add_deletion_schedule,update_schedule_status,clear_database,get_job_id_by_username,get_all_schedules
from config import channel_id

router = Router()
scheduler = AsyncIOScheduler()

class ScheduleDeletion(StatesGroup):
    waiting_usernames = State()
    waiting_time_schedule = State()
    waiting_username = State()

async def deleting_users_schedule(user_name):
    try:
        job_id = await get_job_id_by_username(user_name)
        print(f"смена статуса {job_id}")
        await update_schedule_status(job_id,"завершено")
        user = await telethon_client.get_entity(user_name)
        user_id = user.id
        await telethon_client(EditBannedRequest(channel_id, user_id, ChatBannedRights(until_date=None, view_messages=True)))
        await asyncio.sleep(1)
        await telethon_client(EditBannedRequest(channel_id, user_id, ChatBannedRights(until_date=None, view_messages=False)))
        print(f"Удален: {user_name}")
    except Exception as e:
            await update_schedule_status(job_id,"не удалось удалить")
            print(f"Ошибка при удалении {user_name}: {e}")

@router.message(lambda message: message.text == "⏳Удалить пользователей через...")
async def choose_deletion_schedule(message: Message, state: FSMContext):
    # await clear_database()
    admins =  await get_admins_and_owner(message,channel_id)
    if admins:
        await message.answer("Введите usernames пользователей через пробел для удаления через:")
        await state.set_state(ScheduleDeletion.waiting_usernames)
    else:
        await message.answer("У вас не достаточно прав для этой операции")

@router.message(ScheduleDeletion.waiting_usernames)
async def saving_list_usernames(message: Message, state: FSMContext):
    list_usernames = message.text.split()
    invalid_users = []
    valid_users = []
    for user_name in list_usernames:
        try:
            user = await telethon_client.get_entity(user_name)
            permissions = await telethon_client.get_permissions(channel_id,user.id)
            valid_users.append(user_name)
        except Exception as e:
            invalid_users.append(user_name)

    if invalid_users:
        error_message = f"Эти пользователи не найдены в канале:\n" + "\n".join(invalid_users)
        await message.answer(error_message)
    
    if not valid_users:
        await message.answer("Нет пользователей для удаления!")
        await state.clear()
        return
    
    await message.answer("Пользователи которые будут удалены:\n"+"\n".join(valid_users))
    await state.update_data(users_names=valid_users)
    await message.answer("Выберите срок удаления:",reply_markup=schedule_buttons())
    await state.set_state(ScheduleDeletion.waiting_time_schedule)
   

@router.message(ScheduleDeletion.waiting_time_schedule)
async def schedule_user_deletion(message: Message, state: FSMContext):
    data = await state.get_data()
    users_names = data.get("users_names", [])

    if not users_names:
        await message.answer("Ошибка: нет пользователей для удаления.")
        await state.clear()
        return
    
    periods = {"🗑️Удалить через 1 мес":1,
        "🗑️Удалить через 3 мес":2,
        "🗑️Удалить через 6 мес":3,
        "🗑️Удалить через 1 год":4
        }

    if message.text in periods:
        day = periods[message.text]
        if not scheduler.running:
            scheduler.start()  
            print("Планировщик был запущен!")
        run_date = datetime.now() + timedelta(minutes=day) 
        for user_name in users_names:
            job = scheduler.add_job(deleting_users_schedule, "date", run_date=run_date, kwargs={"user_name": user_name})
            job_id = job.id
            await add_deletion_schedule(user_name, run_date,job_id)
            print(job_id)
            print(users_names)
        await message.answer(f"Пользователи будут удалены {run_date.strftime('%Y-%m-%d %H:%M:%S')}.")
        # Сохраняем job_id в состоянии, чтобы потом можно было отменить задачу
        await state.clear()
        # Сохраняем задачу в БД (для персистентности графика)
        await state.update_data(jobid=job_id)
    else:
        await message.answer("Некорректный выбор времени.")
        await state.clear()

        
       

@router.message(lambda message: message.text == "🚫 Отменить удаление")
async def cancel_deletion_start(message: Message, state: FSMContext):
    # Запускаем процедуру отмены – запрашиваем username, для которого нужно отменить задачу
    await message.answer("Введите username, для которого нужно отменить удаление:")
    await state.set_state(ScheduleDeletion.waiting_username)

@router.message(ScheduleDeletion.waiting_username)
async def cancel_deletion_handler(message: Message, state: FSMContext):
   user_list = message.text.strip().split()
   for user_name in user_list:
        job_id = await get_job_id_by_username(user_name)

        if not job_id:
            await message.answer(f"Для {user_name} нет активных задач.")
            continue

        try:
            if scheduler.get_job(job_id):
                scheduler.remove_job(job_id)
                await update_schedule_status(job_id, "отменено")
                await message.answer(f"Удаление для @{user_name} отменено.")
            else:
                await message.answer(f"Задача для @{user_name} уже отменена.")
        except Exception as e:
            await message.answer(f"Ошибка отмены для @{user_name}: {e}")
        await state.clear()


async def restore_scheduled_jobs():
    schedules = await get_all_schedules()
    for schedule in schedules:
        job_id, user_name, scheduled_time_str, status, created_at = schedule
        
        # Восстанавливаем только задачи со статусом "scheduled"
        if status != "scheduled":
            continue

        scheduled_time = datetime.fromisoformat(scheduled_time_str)
        current_time = datetime.now()

        # Если время задачи уже прошло
        if scheduled_time < current_time:
            await update_schedule_status(job_id, "просрочено")
            print(f"Задача {job_id} для {user_name} просрочена.")
            continue  # Не добавляем в планировщик

        # Восстанавливаем задачу
        try:
            job = scheduler.add_job(
                deleting_users_schedule,
                "date",
                run_date=scheduled_time,
                kwargs={"user_name": user_name},
                id=job_id  # Используем существующий job_id
            )
            print(f"Восстановлена задача для {user_name} (ID: {job.id})")
        except Exception as e:
            print(f"Ошибка восстановления задачи {job_id}: {e}")
            await update_schedule_status(job_id, "ошибка восстановления")