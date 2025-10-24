from discord.ext import commands
import api
from log import *
from typing import *
from config import *
from aiogram import Router
from aiogram.filters import Command, CommandStart, CommandObject
import aiogram


# telegram bot

router = Router()
dcbot: commands.Bot = None
manager: api.Manager = None


@router.message(CommandStart(True))
async def on_message(message: aiogram.types.Message, command: CommandObject):
    if not command.args:
        return
    
    code = command.args
    user = manager.confirm_tg_link_key(message.from_user.id, code)

    if not user:
        return
    
    name = dcbot.get_user(user.id)
    usertext = ''
    if name:
        usertext = f'\n\n<b>{name.name}</b>, верно?'
    
    # confirming
    await message.reply(
        f'<b>👋 Привет!</b>{usertext}\n\nТеперь твои аккаунты успешно связаны.'\
        '\nОтвязать можно по команде <b>ml!link</b> в Discord.'
    )



@router.message(Command('link'))
async def on_message(message: aiogram.types.Message):
    if message.chat.type != 'private':
        return
    
    if len(message.text.split()) != 2:
        return
    
    code = message.text.split()[1]
    user = manager.confirm_tg_link_key(message.from_user.id, code)

    if not user:
        return
    
    name = dcbot.get_user(user.id)
    usertext = ''
    if name:
        usertext = f'\n\n<b>{name.name}</b>, верно?'
    
    # confirming
    await message.reply(
        f'<b>👋 Привет!</b>{usertext}\n\nТеперь твои аккаунты успешно связаны.'\
        '\nОтвязать можно по команде <b>ml!link</b> в Discord.'
    )