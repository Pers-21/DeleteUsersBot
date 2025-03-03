from aiogram.types import Message
from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup,State
from commands_buttons.buttons import button
from telethon import TelegramClient
from config import api_id,api_hash
from telethon.tl.types import ChatBannedRights
from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChannelParticipantsAdmins, ChannelParticipantCreator
from config import channel_id


router = Router()
telethon_client = TelegramClient('telethon_session',api_id,api_hash)


class DeleteUsersState(StatesGroup):
    waiting_for_usernamaes = State() 
    deleting_users = State()



@router.message(lambda message:message.text == "🗑️Удалить пользователей сейчас")
async def handler_deleting_users(message:Message,state:FSMContext):
    admins = await get_admins_and_owner(message,channel_id)
    if admins:
        await message.answer("Введите usernams пользывателей")
        await state.set_state(DeleteUsersState.waiting_for_usernamaes)
    else:
        await message.answer("У вас не достаточно прав для этой операции")



@router.message(DeleteUsersState.waiting_for_usernamaes)
async def saving_list_usernames(message:Message,state:FSMContext):
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
        error_message = f"Эти пользователи не является участниками канала:\n" + "\n".join(invalid_users)
        await message.answer(error_message)
    

    if not valid_users:
        await message.answer("Нет пользователей для удаления!")
        await state.clear()
        return
    
    await message.answer("Пользователи которые будут удалены:\n"+"\n".join(valid_users))
    await state.update_data(usersnames=valid_users)    
    await deleting_users(message,state)
   


async def get_userid_by_username(state:FSMContext):
    data = await state.get_data()
    list_usernames = data.get("usersnames")
    users_ids = []
    for username in list_usernames:
        user_id = await telethon_client.get_entity(username)
        if user_id:
            users_ids.append(user_id.id)
    return users_ids    


async def deleting_users(message:Message,state:FSMContext):
    users_ids = await get_userid_by_username(state)
    for user_id in users_ids:
        await telethon_client(EditBannedRequest(channel_id,user_id,ChatBannedRights(until_date=None,view_messages=True)))
        await telethon_client(EditBannedRequest(channel_id,user_id,ChatBannedRights(until_date=None,view_messages=False)))
    await message.answer("Пользыватели удалены")
    await state.clear()


async def get_admins_and_owner(message:Message,channel_id):
    admins = []
    owner_id = None
    
    async for user in telethon_client.iter_participants(
        channel_id,
        filter=ChannelParticipantsAdmins() 
    ):
        if isinstance(user.participant, ChannelParticipantCreator):
            owner_id = user.id
        else:
            admins.append(user.id)

    if  message.from_user.id in admins or  message.from_user.id == owner_id:
            return True
    else:
            return False



