
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


@router.message(Command('help'))
async def on_message(message: aiogram.types.Message):
    # filtering
    if not message.from_user: return

    await message.reply('Ок', reply_markup=aiogram.types.ReplyKeyboardRemove())