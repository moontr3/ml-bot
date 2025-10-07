import aiohttp
from discord.ext import commands
import discord
import api
from log import *
from typing import *
from config import *
import utils
from bot import MLBot
import datetime
import os


# setup
async def setup(bot: MLBot):
    
    @bot.command(
        name='partner2'
    )
    async def partner_msg(ctx: commands.Context):
        view = to_container([
            # '### :loudspeaker: пожалуй в этот раз пропустим все приветы и перейдем сразу к смаку - **что вообще за мунленд?**',
            ui.MediaGallery(discord.MediaGalleryItem('attachment://text.png')), 
            SEP(visible=False), ui.MediaGallery(discord.MediaGalleryItem('attachment://bar.png')), SEP(visible=False),
            '### у нас тут есть:',
            ':speaking_head: разговоры на **нишевые темы** (и часто программирование (ну и ненишевые тоже есть да))',
            ':books: **нестрогие и короткие правила** - можно не бояться мута и быть собой',
            ':speaker: частые посиделки в войсах ||без микро||',
            ':sparkles: уникальная **система левелинга и репутации** которую не найдете на любом другом сервере',
            ':robot: Мега Эпичный Кастомный **Мунленд Бот с игрульками**',
            ':slot_machine: **Лудомания** (к сожалению понарошку)',
            ':busts_in_silhouette: крутые **сигма участники** (проверено)',
            ':bar_chart: рандомные необычные **ивентики и происходилки**',
            ':nazar_amulet: _~~сысыкутариканыктинак...~~_',
            SEP(visible=False), ui.MediaGallery(discord.MediaGalleryItem('attachment://bar.png')), SEP(visible=False),
            to_container([
                'в общем поделать тут есть что - можно собирать скины для **преукрашивания своего профиля** в таблице лидеров, '\
                    '**батлиться** с другими участниками или просто **общаться** :thumbsup:'
            ], accent_color=discord.Color.from_str('#641CBC')),
            SEP(visible=False), ui.MediaGallery(discord.MediaGalleryItem('attachment://bar.png')), SEP(visible=False),
            '#  <:em1:1411447501055070349><:em2:1411447490875625603> '\
                '[заходи, не заскучаешь (нажми)](https://discord.gg/s3NrXyYjnG) '\
                '<:em3:1411447512631611453><:em4:1411447525704990720>',
            SEP(visible=False), ui.MediaGallery(discord.MediaGalleryItem('attachment://banner.png')),
        ], no_container=True)

        files = [
            discord.File('./assets/bar.png', filename='bar.png'),
            discord.File('./assets/text.png', filename='text.png'),
            discord.File('./assets/banner.png', filename='banner.png'),
        ]
        await ctx.send(view=view, files=files)


    @bot.command(
        name='partner'
    )
    async def partner_msg(ctx: commands.Context):
        view = to_container([
            ui.MediaGallery(discord.MediaGalleryItem('attachment://sex.png')),
            'предложить не могу, но крутой дискорд сервер у нас есть',
            SEP(visible=False), ui.MediaGallery(discord.MediaGalleryItem('attachment://bar.png')), SEP(visible=False),
            '## <:em1:1411447501055070349><:em2:1411447490875625603> '\
                '[moonland:re](https://discord.gg/s3NrXyYjnG) '\
                '<:em3:1411447512631611453><:em4:1411447525704990720>',
        ], no_container=True)

        files = [
            discord.File('./assets/bar.png', filename='bar.png'),
            discord.File('./assets/СЕКС.png', filename='sex.png'),
        ]
        await ctx.send(view=view, files=files)


    @bot.hybrid_command(
        name='ping',
        aliases=['пинг'],
        description='Показывает пинг бота.'
    )
    @api.check_guild
    @discord.app_commands.guild_only()
    @discord.app_commands.guild_install()
    async def slash_ping(ctx: commands.Context):
        '''
        Shows bot ping.
        '''
        log(f'{ctx.author.id} requested bot ping')
        ping = round(bot.latency*1000)
        view = to_view([
            '### 🏓 Понг!', SEP(), f'**{ping}** мс'
        ])
        await ctx.reply(view=view)


    @bot.hybrid_command(
        name='invites',
        aliases=['invite','инвайты','инвайтов','инвайт'],
        description='Показывает количество использовний ссылки-приглашения.'
    )
    @api.check_guild
    @discord.app_commands.guild_only()
    @discord.app_commands.guild_install()
    async def slash_invite(ctx: commands.Context):
        '''
        Shows invite count.
        '''
        log(f'{ctx.author.id} requested invite count')

        invites = 0
        invitelist = await ctx.guild.invites()

        for i in invitelist:
            invites += i.uses
        
        view = to_view(f'# {utils.to_cool_numbers(invites)}')
        await ctx.reply(view=view)


    @bot.hybrid_command(
        name='moonland',
        description='💜 Отправить ссылку-приглашение на moonland:re'
    )
    @discord.app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @discord.app_commands.allowed_installs(guilds=False, users=True)
    async def slash_invite(ctx: commands.Context):
        log(f'{ctx.author.id} sending invite')

        view = to_view([
            '**moonland bot** - бот сервера moonland:re.',
            '## https://discord.gg/s3NrXyYjnG'
        ], discord.Color.from_str('#641CBC'))

        await ctx.reply(view=view, ephemeral=True)


    @bot.hybrid_command(
        name='stats',
        aliases=['стат','стата','статистика','stat','statistics'],
        description='Показывает вашу статистику на сервере.'
    )
    @api.check_guild
    @discord.app_commands.guild_only()
    @discord.app_commands.guild_install()
    async def slash_about(ctx: commands.Context, user: discord.User=None):
        '''
        Shows bot info.
        '''
        log(f'{ctx.author.id} requested bot info')

        if user == None:
            user = ctx.author

        if user.bot:
            view = to_view('Это бот да. незя атата', ERROR_C)
            await ctx.reply(view=view)
            return

        botuser: api.User = bot.mg.get_user(user.id)
        finishes = bot.mg.get_lb_finishes(user.id)
        
        view = to_view([
            f'### 📊 Статистика {user.display_name}', SEP(),
            f'### {PLACE1} **{finishes[1]}** ・ {PLACE2} **{finishes[2]}** ・ {PLACE3} **{finishes[3]}**',
            f'Поставлено напоминаний: **{len(botuser.reminders)} / {MAX_REMINDERS}**',
            f'Режим Зверя: {"✅" if botuser.marked_by_beast else "❌"}',
            f'Likee Bot: {"✅" if botuser.likee else "❌"}',
        ])
        await ctx.reply(view=view)


    @bot.tree.command(
        name='anon',
        description='Отправляет анонимное сообщение в #чат.'
    )
    @discord.app_commands.guild_only()
    @discord.app_commands.guild_install()
    @discord.app_commands.describe(text='Текст сообщения')
    async def slash_anon(ctx: discord.Interaction, text: str):
        '''
        Sends anonymous message.
        '''
        if not ctx.guild:
            return
        if ctx.guild.id != GUILD_ID:
            return
        
        if ctx.channel.id != CHAT_CHANNEL:
            view = to_view(f'Эта команда доступна только в канале <#{CHAT_CHANNEL}>.', ERROR_C)
            await ctx.response.send_message(view=view, ephemeral=True)
            return

        if 'discord.com/invite/' in text.lower() or 'discord.gg/' in text.lower():
            view = to_view('Нет иди нахуй', ERROR_C)
            await ctx.response.send_message(view=view, ephemeral=True)
            return
        
        await ctx.response.defer(ephemeral=True)

        # sending
        await bot.service_webhook.send(
            content=text, username='Анонимное сообщение ・ /anon',
            avatar_url=MESSAGE_IMAGE, allowed_mentions=NO_MENTIONS
        )

        log(f'{ctx.user.id} sent an anonymous message: {text}')

        # success
        view = to_view('Сообщение отправлено!', DEFAULT_C)
        await ctx.followup.send(view=view)


    @bot.hybrid_command(
        name='about',
        aliases=['info','оботе','инфо','информация'],
        description='Показывает информацию о боте.'
    )
    @api.check_guild
    @discord.app_commands.guild_only()
    @discord.app_commands.guild_install()
    async def slash_about(ctx: commands.Context):
        '''
        Shows bot info.
        '''
        log(f'{ctx.author.id} requested bot info')

        stats = bot.mg.get_all_info()
        verified_count = len(ctx.guild.get_role(VERIFY_ROLE).members)
        
        view = to_view([
            '### :information_source: О боте', SEP(),
            'Создатель: `moontr3` (obviously)',
            'Контрибьюторы: `n0n1m`, `mbutsk`',
            'Написан на **Python** и **discord.py**\n-# Рендеринг картинок через **pygame-ce**',
            SEP(),
            f'Пользователей зарегистрировано: **{len(bot.mg.users)}**',
            f'Участников на сервере: **{ctx.guild.member_count}**',
            f'Верифицировано: **{verified_count}**',
            SEP(),
            f'Всего заработано опыта: **{stats["xp"]} XP**',
            f'Всего получено скинов: **{stats["skins"]}**',
            f'Всего получено шрифтов: **{stats["fonts"]}**',
            f'Всего собрано Q: **{stats["q"]} Q**',
        ])

        await ctx.reply(view=view)


    # purge command
    @bot.hybrid_command(
        name='purge',
        aliases=['очистить'],
        description='👩‍⚖️ Удаляет определенное количество сообщений в канале.'
    )
    @api.check_guild
    @discord.app_commands.guild_only()
    @discord.app_commands.guild_install()
    @discord.app_commands.describe(
        amount='Количество сообщений для очистки',
        member='Фильтр для удаления сообщений только указанного участника',
        keywords='Фильтр для удаления сообщений только с нужным текстом'
    )
    async def slash_purge(
        ctx: commands.Context, amount:int,
        member:discord.User=None, keywords:str=''
    ):
        '''
        Purges the channel.
        '''
        # checking permissions
        if not ctx.permissions.manage_messages:
            await ctx.reply(view=c_to_view(MISSING_PERMS_EMBED))
            return
        
        # sending loading message
        await ctx.reply(view=c_to_view(LOADING_EMBED))

        # just purge
        if member == None and keywords == '':
            deleted = await ctx.channel.purge(limit=amount)
            text = f'Успешно очищено **{len(deleted)}** сообщений!'

        # filter by user
        elif member != None and keywords == '':
            def check(m):
                return m.author.id == member.id
            
            deleted = await ctx.channel.purge(limit=amount, check=check)
            text = f'Успешно очищено **{len(deleted)}** сообщений от {member.name}!'

        # filter by keywords
        elif member == None and keywords != '':
            def check(m):
                return keywords in m.content
            
            deleted = await ctx.channel.purge(limit=amount, check=check)
            text = f'Успешно очищено **{len(deleted)}** из **{amount}** проверенных сообщений!'
        
        # both
        else:
            def check(m):
                return (keywords in m.content) and\
                    (m.author.id == member.id)
            
            deleted = await ctx.channel.purge(limit=amount, check=check)
            text = f'Успешно очищено **{len(deleted)}** сообщений от {member.name}!'

        log(f'{ctx.author.id} purged {len(deleted)}/{amount} messages in {ctx.channel.id}')

        # sending message
        # checking if there even was something deleted
        if len(deleted) == 0:
            view = to_view([
                '🗑 Очистка', SEP(),
                'По такому запросу не найдено сообщений, которые можно удалить.'
            ], ERROR_C)
        else:
            view = to_view([
                '🗑 Очистка', SEP(), text
            ], DEFAULT_C)
        await ctx.response.edit_message(view=view)


    # mute command

    @bot.hybrid_command(
        name='mute',
        aliases=['мут','timeout','таймаут'],
        description='👩‍⚖️ Мутит определенного участника на сервере.'
    )
    @api.check_guild
    @discord.app_commands.guild_only()
    @discord.app_commands.guild_install()
    @discord.app_commands.describe(
        member='Участник, которого нужно замутить',
        length='Длина мута в формате "10h", "3д" и так далее',
        reason='Причина мута'
    )
    async def slash_mute(
        ctx: commands.Context, member:discord.Member,
        length:str, *, reason:str=None
    ):
        '''
        Mutes the specified user.
        '''
        # checking permissions
        if not ctx.permissions.moderate_members:
            await ctx.reply(view=c_to_view(MISSING_PERMS_EMBED))
            return

        # muting user
        data = utils.seconds_from_string(length)
        # checking input validity
        if data == None:
            await ctx.reply(view=c_to_view(INCORRECT_LENGTH_EMBED), ephemeral=True)
            return
        
        else:
            length = data[0]
            unit_name = data[1]
            unit_length = data[2]

        length = datetime.timedelta(seconds=length)
        
        # timeouting user
        try:
            await member.timeout(length, reason=reason)
            log(f'{ctx.author.id} timeouted user {member.id} for {length}')
        
        except Exception as e:
            log(f'Error while {ctx.author.id} was timeouting {member.id} for {length}: {e}', level=ERROR)
            view = to_view('Не удалось замутить участника.', ERROR_C)
            await ctx.reply(view=view, ephemeral=True)
            return

        # sending message
        if reason == None:
            view = to_view([
                '### 🤐 Таймаут', SEP(),
                f'{member.name} успешно замьючен на **{unit_length} {unit_name}**.'
            ], DEFAULT_C)

        else:
            view = to_view([
                '### 🤐 Таймаут', SEP(),
                f'{member.name} успешно замьючен на **{unit_length} {unit_name}** '\
                    f'по причине **{reason}**.'
            ], DEFAULT_C)

        await ctx.reply(view=view)


    # unmute command
    @bot.hybrid_command(
        name='unmute',
        aliases=['размут','анмут'],
        description='👩‍⚖️ Размучивает определенного участника на сервере.'
    )
    @api.check_guild
    @discord.app_commands.guild_only()
    @discord.app_commands.guild_install()
    @discord.app_commands.describe(
        member='Участник, которого нужно размутить'
    )
    async def slash_unmute(
        ctx: commands.Context, member:discord.Member
    ):
        '''
        Unmutes the specified user.
        '''
        # checking permissions
        if not ctx.permissions.moderate_members:
            await ctx.reply(view=c_to_view(MISSING_PERMS_EMBED))
            return

        # checking if the user is muted or not
        if member.timed_out_until == None:
            view = to_view('Этот участник и так не в муте.', ERROR_C)
            await ctx.reply(view=view, ephemeral=True)
            return

        # unmuting
        try:
            await member.timeout(None)
            log(f'{ctx.author.id} unmuted user {member.id}')

        except Exception as e:
            log(f'Error while {ctx.author.id} was unmuting {member.id}: {e}', level=ERROR)
            view = to_view('Не удалось размутить участника.', ERROR_C)
            await ctx.reply(view=view, ephemeral=True)
            return
           
        view = to_view([
            '### 🤐 Размут', SEP(),
            f'Вы успешно размутили {member.name}!'
        ], DEFAULT_C)
        await ctx.reply(view=view)
