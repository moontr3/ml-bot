import aiohttp
from discord.ext import commands
import discord
import api
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
        if not  message.guild or message.guild.id != GUILD_ID:
            return
        
        # resolving interation author
        user = message.author

        if message.interaction_metadata:
            orig_user = message.interaction_metadata.user

            user = message.guild.get_member(orig_user.id)
            if user == None:
                user = await message.guild.fetch_member(orig_user.id)

        botuser: api.User = bot.mg.get_user(user.id)

        # checking for violations
        if isinstance(user, discord.User):
            return
        
        if user.get_role(IMBA_ROLE) or botuser.xp.xp > XP_THRESHOLD:
            return
        
        reason = []
        
        if len(message.mentions) > 3:
            reason.append(f'{len(message.mentions)} пингов в сообщ')

        if 'discord.gg/' in message.content.lower():
            reason.append('Ссылка на сервер')

        if message.author.id in PIDORAS_ID:
            reason.append(f'Использование {message.author.name}')
            
        if reason:
            log(f'Reason to ban {user.name} {user.id} - {", ".join(reason)}')

            # deleting message
            try:
                await message.delete()
            except Exception as e:
                log('Error deleting message: ' + str(e), level=ERROR)

            # banning user
            try:
                await user.ban(
                    reason=f'Автор: {message.author.name} - {message.author.id} {", ".join(reason)}',
                    delete_message_days=0
                )
            except Exception as e:
                log('Error banning user: ' + str(e), level=ERROR)

            # sending log message
            try:
                session = aiohttp.ClientSession()
                webhook = discord.Webhook.from_url(bot.WEBHOOK, session=session)
                
                elements = [
                    message.content if message.content else None,
                    SEP(spacing=discord.SeparatorSpacing.large),
                    f'{message.channel.mention} ・ {message.channel.id}',
                    f'{user.mention} ・ {user.id}'
                ]
                if message.author != user:
                    elements.append(f'🤖 {user.mention} ・ {user.id}')
                
                elements.append(SEP())
                elements.extend(reason)

                view = to_view(elements)
                mentions = discord.AllowedMentions(users=False, everyone=False, roles=False, replied_user=False)

                await webhook.send(view=view, username='Удалён спам', avatar_url=WARN_IMAGE, allowed_mentions=mentions)
                await session.close()

            except Exception as e:
                log('Error sending report to logs: ' + str(e), level=ERROR)