from discord.ext import commands
import discord
from data import *
from log import *
from typing import *
from config import *

# setup
async def setup(bot: commands.Bot):
    @bot.event
    async def on_ready():
        log('Ready!', level=SUCCESS)

    @bot.event
    async def on_disconnect():
        log('Disconnected', level=WARNING)

    @bot.event
    async def on_connect():
        log('Connected')

    @bot.event
    async def on_resumed():
        log('Resumed', level=SUCCESS)
