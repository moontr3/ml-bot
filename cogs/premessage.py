
import discord
from log import *
from typing import *
from config import *
from bot import MLBot
from .ai import check_ai


# setup
async def setup(bot: MLBot):

    @bot.event
    async def on_message(message: discord.Message):
        if message.author.id == bot.user.id:
            return
        
        if message.guild == None:
            await message.reply(view=c_to_view(NO_DM_EMBED))
            return
        
        if message.content.startswith('.'):
            await bot.process_commands(message)
            return

        await bot.process_commands(message)
        
        if bot.features.ai:
            await check_ai(bot, message)