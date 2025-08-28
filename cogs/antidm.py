
from discord.ext import commands
import discord
from log import *
from typing import *
from config import *
import api
import utils


# setup
async def setup(bot: commands.Bot):

    @bot.event
    async def on_message(message: discord.Message):
        if message.author.bot:
            return

        if message.guild == None:
            await message.reply(view=c_to_view(NO_DM_EMBED))
            return
        
        await bot.process_commands(message)