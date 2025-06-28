from discord.ext import commands
import discord
from log import *
from typing import *
from config import *
import utils
import datetime
import os


# setup
async def setup(bot: commands.Bot):

    @bot.listen()
    async def on_message(message: discord.Message):
        if message.author.id in PIDORAS_ID:
            if message.interaction_metadata:
                user = message.interaction_metadata.user
                try:
                    user = message.guild.get_member(user.id)
                    if user == None:
                        user = await message.guild.fetch_member(user.id)

                    if user.is_timed_out():
                        await message.delete()
                        return
                    
                    # timing out user
                    if message.guild.get_role(IMBA_ROLE) in user.roles:
                        length = datetime.timedelta(minutes=1)
                    else:
                        length = datetime.timedelta(days=1)

                    await user.timeout(length=length, reason=f'Using {message.author.name}')
                    log(f'Timed out user {user.id} for using {message.author.name} ({length.seconds//60} mins)')

                except Exception as e:
                    log(f'Unable to timeout user {user.id} for using {message.author.name}: {e}', level=ERROR)

            else:
                await message.delete()