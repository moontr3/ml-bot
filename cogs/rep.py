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

        # checking for rep command
        for command, amount in REP_COMMANDS.items():
            if not message.content.lower().startswith(command.lower()):
                continue
            
            # checking message answer
            if message.reference == None:
                embed = discord.Embed(
                    description='Надо __ответить на сообщение__,', color=ERROR_C
                )
                return await message.reply(embed=embed)

            try:
                reference = await message.channel.fetch_message(message.reference.message_id)
            except:
                return
            
            if reference.author == message.author:
                embed = discord.Embed(
                    description='Нельзя репать свои сообщения!', color=ERROR_C
                )
                return await message.reply(embed=embed)

            if reference.author.bot: 
                embed = discord.Embed(
                    description='У ботов нет репутации!', color=ERROR_C
                )
                return await message.reply(embed=embed)

            # rep adding / removing
            if amount not in REP_EMOJIS: return
            emoji = REP_EMOJIS[amount]

            log(f'{reference.author.id} got {amount} rep from {message.author.id}')
            bot.mg.add_rep(reference.author.id, amount)

            await message.delete()
            try:
                await reference.add_reaction(emoji)
            except:
                pass

            return
    

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