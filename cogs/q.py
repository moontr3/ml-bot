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
    
    @bot.hybrid_command(
        name='bal',
        description='Посмотреть количество пойманных Q.',
        aliases=['balance','b','баланс','бал','б']
    )
    @discord.app_commands.guild_only()
    @discord.app_commands.describe(
        user='Пользователь, Q которого вы хотите узнать.'
    )
    async def me(ctx: commands.Context, user: discord.User = None):
        user = ctx.author if user == None else user

        if ctx.interaction:
            await ctx.interaction.response.defer()
        else:
            await ctx.channel.typing()

        path = bot.mg.renderer.q_level(user)
        file = discord.File(path, 'image.png')
        await ctx.reply(file=file)

        file.close()
        os.remove(path)


    @bot.command(
        name='q',
        description='q'
    )
    async def manual_q(ctx: commands.Context, admin: str = None):
        '''
        Places a Q on a message.
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
            view = to_view('Надо ответить на сообщение, на которое хотите поставить :regional_indicator_q:.', ERROR_C)
            await ctx.reply(view=view)
            return

        # yaay success
        await ctx.message.delete()
        await fetched.add_reaction('🇶')

        if ctx.author.id in ADMINS and admin == 'admin':
            log(f'manually spawning Q in {fetched.channel.id} (msg {fetched.id})')
            bot.mg.unclaimed_qs[fetched.id] = api.UnclaimedQ(fetched.id)


    # randomly setting reaction
    @bot.listen()
    async def on_message(message: discord.Message):
        if random.random() > Q_CHANCE:
            return
        
        await message.add_reaction('🇶')

        if message.channel.id in CHATTABLE_CHANNELS:
            bot.mg.unclaimed_qs[message.id] = api.UnclaimedQ(message.id)
            log(f'spawning Q in {message.channel.id} (msg {message.id})')


    # claiming Qs
    @bot.listen()
    async def on_raw_reaction_add(reaction: discord.RawReactionActionEvent):
        if reaction.message_id not in bot.mg.unclaimed_qs: return
        qdata: api.UnclaimedQ = bot.mg.unclaimed_qs[reaction.message_id]

        channel = bot.get_channel(reaction.channel_id)
        message = await channel.fetch_message(reaction.message_id)

        # checking if 30 mins have passed
        if time.time()-message.created_at.timestamp() > 60*30:
            return
        
        # checking emoji
        if reaction.emoji.name != '🇶':
            return
        
        log(f'{reaction.user_id} tries to collect Q in {reaction.channel_id}')

        # checking if user collected this emoji
        if reaction.user_id in qdata.claimed:
            return
        
        # success
        log(f'{reaction.user_id} collected Q')
        qdata.claimed.append(reaction.user_id)
        bot.mg.add_q(reaction.user_id, 1)