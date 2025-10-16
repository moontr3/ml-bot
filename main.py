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
from cogs import tg_cogs

# loading token

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
bots = []

# telegram bot

TG_TOKEN = os.getenv('TG_TOKEN')
tg_bot = None

if TG_TOKEN:
    tg_bot = Bot(TG_TOKEN, default=DefaultBotProperties(
        parse_mode="HTML"
    ))
    dp = Dispatcher()
    for i in tg_cogs.routers:
        dp.include_router(i.router)

    bots.append(dp.start_polling(tg_bot))

# discord bot

bot = MLBot(command_prefix=PREFIXES, intents=discord.Intents.all(), help_command=None, tg_bot=tg_bot)
bots.append(bot.start(TOKEN))

if tg_bot:
    for i in tg_cogs.routers:
        i.dcbot = bot
        i.manager = bot.mg

# running bots

async def main():
    await asyncio.gather(*bots)

asyncio.run(main())