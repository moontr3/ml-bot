from config import *
from api import *
from log import *
from bot import MLBot

import discord
from discord.ext import commands
import glob
import asyncio
from dotenv import load_dotenv
import os
from typing import *

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from cogs import crossposter

# loading token
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

bot = MLBot(command_prefix=PREFIXES, intents=discord.Intents.all(), help_command=None)

# telegram bot

TG_TOKEN = os.getenv('TG_TOKEN')

tg_bot = Bot(TG_TOKEN, default=DefaultBotProperties(
    parse_mode="HTML"
))
dp = Dispatcher()
bot.tgbot = tg_bot
crossposter.dcbot = bot
crossposter.manager = bot.mg
dp.include_router(crossposter.router)

# running bots

async def main():
    await asyncio.gather(dp.start_polling(tg_bot), bot.start(TOKEN))

asyncio.run(main())