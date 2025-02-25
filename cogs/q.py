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
        # on reply
        try:
            m = await message.channel.fetch_message(
                message.reference.message_id
            )
            if not message.author.bot:
                bot.mg.add_xp(m.author.id, 1)
            reply = 1
        except:
            reply = 0

        additional = 0

        # counting
        if message.channel.id == COUNTER_ID:
            async for i in message.channel.history(limit=2):
                if i.id != message.id:
                    try:
                        if int(i.content) == int(message.content)-1 and\
                        i.author.id != message.author.id:
                            log(f'{message.author.id} counted {int(message.content)} on {i.author.id}')
                            additional += random.randint(2,4)
                    except:
                        pass
                    break

        # Zero
        contains_zero = 'на часах 00' in message.content.lower()
        channel_matches = message.channel.id == ZERO_ID
        message_time = message.created_at+datetime.timedelta(hours=3)
        time_matches = message_time.hour == 0 and message_time.minute == 0

        if contains_zero and channel_matches and time_matches:
            user_check = bot.mg.check_user_zero(message.author.id)
            if user_check:
                additional += random.randint(30,50)

        # message itself
        if message.channel.id in CHATTABLE_CHANNELS:
            to_add = 1 + int(len(message.content)/100)+\
                len(message.attachments)*2 +\
                len(message.embeds) +\
                reply
            to_add = min(10, to_add)
        else:
            to_add = 0
        to_add += additional

        out = bot.mg.add_xp(message.author.id, to_add)

        if out:
            if out < len(LEVELS):
                role = message.guild.get_role(LEVELS[out-1])
                await message.author.add_roles(role)
                embed = discord.Embed(
                    title='Повышение',
                    description=f'Ваш ранг был повышен до **{role.name.capitalize()}**!',
                    color=role.color
                )
            else:
                embed = discord.Embed(
                    title='Повышение',
                    description=f'Ваш уровень был повышен до **{out}**!',
                    color=role.color
                )
            await message.reply(embed=embed)
            
