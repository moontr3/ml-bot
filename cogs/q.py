import random
from discord.ext import commands
import discord
from log import *
from typing import *
from config import *
import utils
import datetime


# setup
async def setup(bot: commands.Bot):

    # q command
    @bot.command(
        name='q',
        description='q'
    )
    async def manual_q(ctx: commands.Context):
        '''
        Responds with Q.
        '''
        log(f'{ctx.author.id} invoked Q command')
        
        # fetching reference
        try:
            fetched = None if ctx.message.reference == None else\
                await ctx.channel.fetch_message(ctx.message.reference.message_id)
        except Exception as e:
            log(f'Error while fetching reference to Q: {e}', level=WARNING)
            fetched = None

        # showing error
        if not fetched:
            embed = discord.Embed(
                title='❌ Ошибка!', color=ERROR_C,
                description=f'Надо __ответить на сообщение__.'
            )
            await ctx.reply(embed=embed)
            return

        # yaay success
        await ctx.message.delete()
        await fetched.add_reaction('🇶')


    # randomly setting reaction
    @bot.listen()
    async def on_message(message: discord.Message):
        if random.random() < 0.05:
            await message.add_reaction('🇶')