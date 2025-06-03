import os
import random
import time
from discord.ext import commands
import discord
import api
from log import *
from typing import *
from config import *
import utils
import datetime


# setup
async def setup(bot: commands.Bot):
    
    @bot.listen('on_message')
    async def rep_earning(message: discord.Message):
        # filtering messages
        if message.author.bot: return
        if message.reference == None: return

        try:
            reference = await message.channel.fetch_message(message.reference.message_id)
        except:
            return
        
        if reference.author == message.author: return
        if reference.author.bot: return

        # checking for rep command
        for command, amount in REP_COMMANDS.items():
            if message.content.lower().startswith(command.lower()):
                # rep adding / removing
                if amount not in REP_EMOJIS: return
                emoji = REP_EMOJIS[amount]

                log(f'{reference.author.id} got {amount} rep from {message.author.id}')
                bot.mg.add_rep(reference.author.id, amount)
                await message.add_reaction(emoji)
    

    @bot.hybrid_command(
        name='rep',
        description='Посмотреть репутацию.',
        aliases=['reputation','реп','репутация']
    )
    @discord.app_commands.describe(
        user='Пользователь, репутацию которого вы хотите узнать.'
    )
    async def rep(ctx: commands.Context, user: discord.User = None):
        user = ctx.author if user == None else user

        if ctx.interaction:
            await ctx.interaction.response.defer()
        else:
            await ctx.channel.typing()

        if user.bot:
            embed = discord.Embed(
                description='Боты не имеют репутацию.', color=ERROR_C
            )
            return await ctx.reply(embed=embed)

        path = bot.mg.renderer.rep(user)
        file = discord.File(path, 'image.png')
        await ctx.reply(file=file)

        file.close()
        os.remove(path)