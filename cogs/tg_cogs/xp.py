
from copy import copy
import os
import random
from discord.ext import commands
import api
from log import *
from typing import *
from config import *
from aiogram import Router
import aiogram
from aiogram.filters import Command


# telegram bot

router = Router()
dcbot: commands.Bot = None
manager: api.Manager = None


@router.message(Command('xp','опыт'))
async def on_message(message: aiogram.types.Message):
    # filtering
    if not message.from_user: return

    user = manager.get_user_by_tg(message.from_user.id)
    if not user:
        await message.reply('Аккаунт не привязан!')
        return
    
    # test
    path = manager.crenderer.user_xp(manager, user)

    await message.reply_photo(aiogram.types.FSInputFile(path))

    os.remove(path)
