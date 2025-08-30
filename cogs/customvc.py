import os
import random
import time
from discord.ext import commands, tasks
import discord
from log import *
from typing import *
from config import *
import api

import utils


# setup
async def setup(bot: commands.Bot):

    @tasks.loop(seconds=1)
    async def temp_vc_activity():
        '''
        Periodically fetches the voice channel state and updates the database
        '''
        guild = bot.get_guild(GUILD_ID)
        to_delete = []

        for channel in guild.voice_channels:
            if channel.id not in bot.mg.temp_vcs:
                continue

            vc: api.TempVC = bot.mg.temp_vcs[channel.id]
            vc.checked = True
            vc.has_people = len(channel.members) > 0

            # renaming
            if vc.name != channel.name:
                log(f'Channel {vc.id} by {vc.owner_id} {vc.name} renamed to {channel.name}')
                vc.name = channel.name

            # activity checker
            if vc.has_people:
                vc.last_activity = time.time()
            elif vc.last_activity+TEMP_VC_INACTIVITY_TIME < time.time():
                to_delete.append(channel.id)
                log(f'Deleting temp VC {channel.id} {channel.name} due to inactivity...')
                await channel.delete()

        # checking other channels and removing nonexistent ones
        for id, i in bot.mg.temp_vcs.items():
            if i.checked:
                i.checked = False
            elif id not in to_delete:
                log(f'Temp VC {i.id} {i.name} not attached to a channel', level=WARNING)
                to_delete.append(id)

        for i in to_delete:
            del bot.mg.temp_vcs[i]
            bot.mg.commit()


    @bot.command()
    async def vchaste(ctx: commands.Context, user: discord.User = None):
        '''
        Removes temp VC timeout.
        '''
        if ctx.author.id not in ADMINS: return
        user = ctx.author if user == None else user
        user: api.User = bot.mg.get_user(user.id)
        user.temp_vc_timeout = 0
        bot.mg.commit()
        
        view = to_view('Yuh-uh.', DEFAULT_C)
        await ctx.reply(view=view)


    @bot.hybrid_command(
        name='temp-vc',
        description='Показывает информацию о вашем созданном временном войсе.',
        aliases=['tvc','tempvc','temp_vc','ввойс','временныйвойс','временный-войс','временный_войс']
    )
    @api.check_guild
    @discord.app_commands.guild_only()
    @discord.app_commands.guild_install()
    async def tvc(ctx: commands.Context):
        '''
        Shows info about the temp VC the user has created.
        '''
        channel: api.TempVC = bot.mg.get_temp_vc(ctx.author.id)

        # no channel
        if channel == None:
            view = to_view([
                '### Вы не создавали временных войсов!', SEP(),
                'Для создания введите `!типо где <название войса>`.'
            ], ERROR_C)
            return await ctx.reply(view=view, ephemeral=True)
        
        # showing info
        # user: api.User = bot.mg.get_user(ctx.author.id)
        desc = None

        if channel.has_people == False:
            desc = f'-# Канал удалится <t:{int(channel.last_activity+TEMP_VC_INACTIVITY_TIME)}:R>'

        view = to_view([
            f'### 🔊 {channel.name}', SEP(),
            f'### <#{channel.id}>',
            f'Канал создал <@{channel.owner_id}> <t:{int(channel.created_at)}:R>',
            desc, '-# Удалить или переименовать канал можно через настройки Discord.'
        ])
        await ctx.reply(view=view)


    @bot.listen()
    async def on_ready():
        if not temp_vc_activity.is_running():
            temp_vc_activity.start()


    @bot.listen()
    async def on_message(message: discord.Message):
        '''
        Checks if there's a command to create a new temp vc.
        '''
        for i in TEMP_VC_CREATE_COMMANDS:
            # telling user how to use the command
            if message.content.lower() == i.lower():
                view = to_view([
                    '### 🔊 Временные войсы', SEP(),
                    f'Используйте `{i} <название>` для создания временного голосового канала.',
                    'Больше информации можно узнать в `ml!faq tvc`.'
                ])
                await message.reply(view=view)
                return

            # using command
            if message.content.lower().startswith(i.lower()):
                name = message.content[len(i):]
                break
        else:
            return
        
        # user already has a channel
        channel = bot.mg.get_temp_vc(message.author.id)

        if channel:
            view = to_view([
                f'Вы уже создали временный канал - <#{channel.id}>!',
                '`ml!tvc` для настроек.'
            ], ERROR_C)
            return await message.reply(view=view)
        
        # user is timeouted
        user: api.User = bot.mg.get_user(message.author.id)
        if user.temp_vc_timeout > time.time():
            view = to_view(
                f'Вы сможете создать временный канал <t:{int(user.temp_vc_timeout)}:R>!', ERROR_C
            )
            return await message.reply(view=view)

        # name is too long
        if len(name) > 100:
            view = to_view(
                'Максимальная длина названия канала - **100 символов**!', ERROR_C
            )
            return await message.reply(view=view)

        # creating temp channel
        category = message.guild.get_channel(TEMP_VC_CATEGORY)
        overwrite = discord.PermissionOverwrite()
        overwrite.manage_channels = True

        role = message.guild.get_role(VERIFY_ROLE)
        role_overwrite = discord.PermissionOverwrite()
        role_overwrite.view_channel = True

        everyone_overwrite = discord.PermissionOverwrite()
        everyone_overwrite.view_channel = False

        quarantine_role = message.guild.get_role(QUARANTINE_ROLE)
        quarantine_overwrite = discord.PermissionOverwrite()
        quarantine_overwrite.view_channel = False
        
        channel = await message.guild.create_voice_channel(
            name, category=category, overwrites={
                message.author: overwrite,
                role: role_overwrite,
                message.guild.default_role: everyone_overwrite,
                quarantine_role: quarantine_overwrite
            }
        )
        log(f"Creating new temp VC {channel.id} - {channel.name} (owner - {user.id})")
        bot.mg.new_temp_vc(channel.name, channel.id, user)

        view = to_view([
            '### 🔊 Временные войсы',
            'Вы создали временный голосовой канал!',
            SEP(),
            f'## <#{channel.id}>',
            SEP(),
            'Используйте `ml!tvc` для просмотра.',
            f'-# Если никто не зайдёт, канал удалится <t:{int(time.time()+TEMP_VC_INACTIVITY_TIME)}:R>.'
        ], DEFAULT_C, text=f'<@&{VC_PING_ROLE}>')
        await message.reply(view=view)
