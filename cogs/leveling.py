import os
import random
from discord.ext import commands, tasks
import discord
from log import *
from typing import *
from config import *
import api
import utils


# setup
async def setup(bot: commands.Bot):

    async def update_rank(member):
        guild = bot.get_guild(GUILD_ID)
        level = bot.mg.get_user(member.id).xp.level
        roles = []
        rank_roles = [guild.get_role(i) for i in LEVELS]

        for i in range(min(len(LEVELS), level)):
            roles.append(rank_roles[i])
        cur_roles = [i for i in member.roles if i.id in LEVELS]

        for i in cur_roles:
            if i not in roles:
                await member.remove_roles(i)

        for i in roles:
            if i not in cur_roles:
                await member.add_roles(i)

        log(f'Edited {member.id} with rank {level}')


    # @discord.app_commands.describe(
    #     member='Участник сервера, у которого нужно поменять опыт.',
    #     action='Действие',
    #     amount='Количество опыта'
    # )
    @bot.command(
        name='manage',
        description='Изменить опыт пользователя.'
    )
    async def slash_manage_xp(ctx: commands.Context, member:discord.User, action:Literal['set','add'], amount:int):
        '''
        Changes user XP level.
        '''
        if ctx.author.id not in ADMINS:
            await ctx.reply(view=c_to_view(NOT_ADMIN_EMBED), ephemeral=True)
            return

        log(f'{ctx.author.id} {action}s xp of {member.id} by {amount}')
        
        if action == 'set':
            new_lvl = bot.mg.set_xp(member.id, amount)
            desc = f'Опыт {member.mention} изменен на **{amount} XP**'
        else:
            new_lvl = bot.mg.add_xp(member.id, amount)
            desc = f'К {member.mention} добавлено **{amount} XP**'

        if new_lvl:
            desc += f'\n\nНовый уровень: **{new_lvl}**'
            await update_rank(member)

        view = to_view(desc, DEFAULT_C)
        await ctx.reply(view=view)


    @bot.command(
        name='reloadroles',
        description='Изменить опыт пользователя.'
    )
    async def slash_manage_xp(ctx: commands.Context, member:discord.User):
        '''
        Relads user XP roles.
        '''
        if ctx.author.id not in ADMINS:
            await ctx.reply(view=c_to_view(NOT_ADMIN_EMBED), ephemeral=True)
            return

        log(f'{ctx.author.id} reloads roles of {member.id}')
        await update_rank(member)

        view = to_view('Yuh-uh.', DEFAULT_C)
        await ctx.reply(view=view)


    @bot.hybrid_command(
        name='calendar',
        aliases=['календарь','cal'],
        description='Показывает календарь опыта участника.'
    )
    @api.check_guild
    @discord.app_commands.guild_only()
    @discord.app_commands.guild_install()
    @discord.app_commands.describe(
        date='Дата в формате ММ.ГГГГ, ГГГГ.ММ, ММ или название месяца.',
        member='Участник сервера, у которого нужно посмотреть календарь опыта.'
    )
    async def slash_calendar(ctx: commands.Context, member:Optional[discord.User]=None, date: str=None):
        '''
        Shows user calendar.
        '''
        if member == None:
            member = ctx.author

        log(f'{ctx.author.id} requested calendar of {member.id}')
        
        if ctx.interaction:
            await ctx.interaction.response.defer()
        else:
            await ctx.channel.typing()

        # checking date
        if date == None:
            day = datetime.datetime.now(datetime.timezone.utc)

        else:
            day = utils.get_datetime(date)

            if day == None:
                view = to_view([
                    '### Некорректный формат даты!', SEP(),
                    'Вводить нужно название месяца или дату в формате `ММ.ГГГГ`, `ГГГГ.ММ` или `ММ`.',
                ], ERROR_C)
                await ctx.reply(view=view, ephemeral=True)
                return

        # sending image
        path = bot.mg.renderer.xp_calendar(member, day.year, day.month)
        file = discord.File(path, 'image.png')
        await ctx.reply(file=file)

        file.close()
        os.remove(path)


    @bot.hybrid_command(
        name='server-calendar',
        description='Показывает календарь опыта сервера.',
        aliases=['scal','скал','server_calendar','servercalendar','серверкалендарь','сервер-календарь','сервер_календарь'],
    )
    @api.check_guild
    @discord.app_commands.guild_only()
    @discord.app_commands.guild_install()
    @discord.app_commands.describe(
        date='Дата в формате ММ.ГГГГ, ГГГГ.ММ, ММ или название месяца.'
    )
    async def slash_server_calendar(ctx: commands.Context, date: str=None):
        '''
        Shows server calendar.
        '''
        log(f'{ctx.author.id} requested server calendar')
        
        if ctx.interaction:
            await ctx.interaction.response.defer()
        else:
            await ctx.channel.typing()

        # checking date
        if date == None:
            day = datetime.datetime.now(datetime.timezone.utc)

        else:
            day = utils.get_datetime(date)

            if day == None:
                view = to_view([
                    '### Некорректный формат даты!', SEP(),
                    'Вводить нужно название месяца или дату в формате `ММ.ГГГГ`, `ГГГГ.ММ` или `ММ`.',
                ], ERROR_C)
                await ctx.reply(view=view, ephemeral=True)
                return

        # sending image
        path = bot.mg.renderer.server_calendar(ctx.author, day.year, day.month)
        file = discord.File(path, 'image.png')
        await ctx.reply(file=file)

        file.close()
        os.remove(path)


    @bot.hybrid_command(
        name='xp',
        aliases=['опыт','lvl','rank','level','уровень','ранк','ранг'],
        description='Показывает текущий опыт пользователя.'
    )
    @api.check_guild
    @discord.app_commands.guild_only()
    @discord.app_commands.guild_install()
    @discord.app_commands.describe(
        member='Участник сервера, у которого нужно узнать опыт.'
    )
    async def slash_xp(ctx: commands.Context, member:discord.User=None):
        '''
        Shows user XP level.
        '''
        if member == None:
            member = ctx.author
        acc: api.User = bot.mg.get_user(member.id)

        log(f'{ctx.author.id} requested xp level of {member.id}')
        role = ctx.guild.get_role(acc.xp.level_data)

        if ctx.interaction:
            await ctx.interaction.response.defer()
        else:
            await ctx.channel.typing()

        path = await bot.mg.renderer.user_xp(member, role)
        file = discord.File(path, 'image.png')
        await ctx.reply(file=file)

        file.close()
        os.remove(path)


    @bot.hybrid_command(
        name='leaders',
        aliases=['лидеры','leaderboard','lb','top','топ'],
        description='Показывает таблицу лидеров по опыту.'
    )
    @api.check_guild
    @discord.app_commands.guild_only()
    @discord.app_commands.guild_install()
    @discord.app_commands.describe(
        board='Нужная таблица лидеров - Всё время, День, Неделя, Сезон, Войс, Микро, Стрим, Q, Реп.'
    )
    async def slash_leaders(ctx:commands.Context, board:str='day'):
        '''
        Shows user XP level.
        '''
        log(f'{ctx.author.id} requested xp leaders')

        if ctx.interaction:
            await ctx.interaction.response.defer()
        else:
            await ctx.channel.typing()

        # board
        boards = {
            "all": "alltime",
            "re": "season",
            ":re": "season",
            "sea": "season",
            "wee": "week",
            "day": "day",
            "tod": "day",
            "все": "alltime",
            "всё": "alltime",
            ":ре": "season",
            "сез": "season",
            "ре": "season",
            "нед": "week",
            "ден": "day",
            "сег": "day",

            "vc": "vc",
            "voi": "vc",
            "str": "stream",
            "liv": "stream",
            "mic": "mic",
            "spe": "mic",
            "вой": "vc",
            "гол": "vc",
            "стр": "stream",
            "мик": "mic",
            "гов": "mic",
            "q": "q",
            "реп": "rep",
            "rep": "rep"
        }

        if board.lower()[:3] not in boards:
            view = to_view([
                '### Такой таблицы лидеров нет!', SEP(),
                'Попробуй одно из:',
                '`День`, `Неделя`, `Сезон`, `Всё время`, `Войс`, `Микро`, `Стрим`, `Q`, `Реп`',
            ], ERROR_C)
            await ctx.reply(view=view, ephemeral=True)
            return
        
        board = boards[board.lower()[:3]]

        # badges
        badges_text = ''

        for i in ['alltime', 'season', 'week', 'day']:
            badges_text += f'{utils.get_lb_badge(i, board == i)}<:no:1358207748294316253>'

        badges_text += '\n' + '<:sep:1358207969472286801>'*11 + '\n'

        for i in ['vc', 'stream', 'mic']:
            badges_text += f'{utils.get_lb_badge(i, board == i)}<:no:1358207748294316253>'

        badges_text += '\n' + '<:sep:1358207969472286801>'*8 + '\n'

        for i in ['rep', 'q']:
            badges_text += f'{utils.get_lb_badge(i, board == i)}<:no:1358207748294316253>'

        # image
        image = await bot.mg.renderer.leaders(ctx.guild, board)
        file = discord.File(image, 'image.png')

        await ctx.reply(badges_text, file=file)
        file.close()
        os.remove(image)


    # gaining xp
    @bot.listen()
    async def on_message(message: discord.Message):
        # checking if bot
        if message.author.bot:
            return
        
        if not message.guild or message.guild.id != GUILD_ID:
            return
        
        bot.mg.set_last_msg_channel(message.author.id, message.channel.id)
        
        botuser = bot.mg.get_user(message.author.id)
        botuser.minute_stats.update_minute()
        
        # on reply
        try:
            assert message.channel.id in CHATTABLE_CHANNELS
            m = await message.channel.fetch_message(
                message.reference.message_id
            )
            if not message.author.bot and not m.author.bot:
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
                        else:
                            await message.delete()
                            return
                    except:
                        await message.delete()
                        return
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
        if message.channel.id in CHATTABLE_CHANNELS and len(message.content) >= MIN_LENGTH_XP:
            to_add = int(len(message.content)/100)+\
                len(message.attachments)*2 +\
                len(message.embeds) +\
                reply
            to_add = min(10, to_add)

            is_one_word = len(message.content.split()) == 1
            if is_one_word:
                botuser.minute_stats.one_word_messages += 1
                if botuser.minute_stats.one_word_messages < ONE_WORD_MSGS:
                    to_add += 1
            else:
                to_add += 1
        else:
            to_add = 0
        to_add += additional

        # minute stats
        if MAX_MINUTE_XP-botuser.minute_stats.xp < to_add:
            to_add = MAX_MINUTE_XP-botuser.minute_stats.xp

        botuser.minute_stats.add_xp(to_add)

        out = bot.mg.add_xp(message.author.id, to_add, False)

        if out:
            if out <= len(LEVELS):
                role = message.guild.get_role(LEVELS[out-1])
                await message.author.add_roles(role)
            else:
                role = None
            
            image = bot.mg.renderer.prom(bot.mg.get_user(message.author.id), out, role) 
            file = discord.File(image, 'image.png')
            await message.reply(file=file)
            file.close()
            os.remove(image)

        
    @tasks.loop(seconds=1)
    async def level_up_loop():
        guild = bot.get_guild(GUILD_ID)

        for user in bot.mg.users.values():
            user: api.User

            if user.to_send_lvl_up_msg:
                if user.xp.level <= len(LEVELS):
                    role = guild.get_role(LEVELS[user.xp.level-1])
                    await guild.get_member(user.id).add_roles(role)

                channel = guild.get_channel(user.last_msg_channel)

                image = bot.mg.renderer.prom(user, user.xp.level, role) 
                file = discord.File(image, 'image.png')
                await channel.send(f'<@{user.id}>', file=file)
                file.close()
                os.remove(image)

                user.to_send_lvl_up_msg = False

    @bot.listen()
    async def on_ready():
        if not level_up_loop.is_running():
            level_up_loop.start()