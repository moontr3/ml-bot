
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
        # caching user data
        bot.mg.cache_user_data(message.author)

        # processing message
        if message.guild == None:
            await message.reply(view=c_to_view(NO_DM_EMBED))
            return

        ctx = await bot.get_context(message)
        if ctx.valid:
            await bot.invoke(ctx)
            return
        
        if message.author.bot:
            return
        
        if bot.features.ai and not message.content.startswith('.'):
            await check_ai(bot, message)