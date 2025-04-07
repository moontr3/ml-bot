import os
import random
from discord.ext import commands
import discord
from log import *
from typing import *
from config import *
import api
from PIL import Image, ImageDraw, ImageFont

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
    async def slash_manage_xp(ctx:commands.Context, member:discord.Member, action:Literal['set','add'], amount:int):
        '''
        Changes user XP level.
        '''
        if ctx.author.id not in ADMINS:
            embed = discord.Embed(
                description='Вы не администратор бота!',
                color=ERROR_C
            )
            await ctx.reply(embed=embed, ephemeral=True)
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

        embed = discord.Embed(
            description=desc, color=DEFAULT_C
        )
        await ctx.reply(embed=embed)


    @discord.app_commands.describe(
        date='Дата в формате ММ.ГГГГ, ГГГГ.ММ, ММ или название месяца.',
        member='Участник сервера, у которого нужно посмотреть календарь опыта.'
    )
    @bot.hybrid_command(
        name='calendar',
        aliases=['календарь','cal'],
        description='Показывает календарь опыта участника.'
    )
    async def slash_calendar(ctx:discord.Interaction, member:Optional[discord.User]=None, date: str=None):
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
                embed = discord.Embed(
                    color=ERROR_C, description='Некорректный формат даты!\n\n'\
                        f'Вводить нужно название месяца или дату в формате `ММ.ГГГГ`, `ГГГГ.ММ` или `ММ`.'
                )
                await ctx.reply(embed=embed, ephemeral=True)
                return

        # sending image
        path = bot.mg.render_xp_calendar(member, day.year, day.month)
        file = discord.File(path, 'image.png')
        await ctx.reply(file=file)

        file.close()
        os.remove(path)


    @discord.app_commands.describe(
        member='Участник сервера, у которого нужно узнать опыт.'
    )
    @bot.hybrid_command(
        name='xp',
        aliases=['опыт','lvl','rank','level','уровень','ранк','ранг'],
        description='Показывает текущий опыт пользователя.'
    )
    async def slash_xp(ctx:discord.Interaction, member:discord.Member=None):
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

        # desc = f'### {role.name.title()} ・ Уровень {acc.xp.level} ・ {acc.xp.xp} XP'\
        #     f'\n**{acc.xp.level_xp}** / **{acc.xp.level_max_xp}** (**{int(acc.xp.level_percentage*100)}%**)'

        # embed = discord.Embed(
        #     description=desc, color=role.color
        # )
        # embed.set_author(name=f'✨ Опыт {member.display_name}')
        # embed.set_image(url='attachment://image.png')

        # if ctx.channel.id not in CHATTABLE_CHANNELS:
        #     embed.set_footer(text='⚠ В этом канале нельзя получать опыт!')

        # bar = regen_bar(member.id, acc.xp.level_xp/acc.xp.level_max_xp)
        # file = discord.File(f'temp/{member.id}.png', 'image.png')

        path = await bot.mg.render_user_xp(member, role)
        file = discord.File(path, 'image.png')
        await ctx.reply(file=file)

        file.close()
        os.remove(path)


    @bot.hybrid_command(
        name='leaders',
        aliases=['лидеры','leaderboard','lb','top','топ'],
        description='Показывает таблицу лидеров по опыту.'
    )
    @discord.app_commands.describe(
        board='Нужная таблица лидеров - Всё время, День, Неделя, Сезон, Войс, Микро, Стрим.'
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

        # ppl = {k: v.xp for k, v in bot.mg.users.items()}
        # ppl = sorted(ppl.items(), key=lambda x: x[1].xp, reverse=True)

        # index = 0
        # counted = 0
        # place = 0
        # prev_xp = -1

        # embed = discord.Embed(
        #     description='🎖 Таблица лидеров', color=DEFAULT_C
        # )

        # while counted < 10:
        #     id = ppl[index][0]
        #     xp = ppl[index][1]

        #     if prev_xp != xp.xp:
        #         place += 1
        #         prev_xp = xp.xp
            
        #     level = xp.level
        #     member = ctx.guild.get_member(id)
        #     if member == None:
        #         index += 1
        #         continue

        #     rank_role = ctx.guild.get_role(LEVELS[min(len(LEVELS)-1, level-1)])

        #     embed.add_field(
        #         name=f'`#{place}` › {member.name}', inline=False,
        #         value=f'**{rank_role.name.capitalize()}** ・ Уровень **{level}** (**{int(xp.level_xp/xp.level_max_xp*100)}%**)'
        #     )
        #     index += 1
        #     counted += 1

        # sum = bot.mg.get_all_xp()
        # embed.set_footer(
        #     text=f'У всех участников суммарно {sum} XP'
        # )

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
            "гов": "mic"
        }

        if board.lower()[:3] not in boards:
            embed = discord.Embed(
                description='Такой таблицы лидеров нет! Попробуй одно из:\n\n'\
                    '`День`, `Неделя`, `Сезон`, `Всё время`, `Войс`, `Микро`, `Стрим`',
                color=ERROR_C
            )
            await ctx.reply(embed=embed, ephemeral=True)
            return
        
        board = boards[board.lower()[:3]]

        # badges
        badges_text = ''

        for i in ['alltime', 'season', 'week', 'day']:
            badges_text += f'{utils.get_lb_badge(i, board == i)}<:no:1358207748294316253>'

        badges_text += '\n' + '<:sep:1358207969472286801>'*11 + '\n'

        for i in ['vc', 'stream', 'mic']:
            badges_text += f'{utils.get_lb_badge(i, board == i)}<:no:1358207748294316253>'

        # image
        image = await bot.mg.render_leaders(ctx.guild, board)
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
            # if role:
            #     role = message.guild.get_role(LEVELS[out-1])
            #     await message.author.add_roles(role)
            #     embed = discord.Embed(
            #         title='Повышение',
            #         description=f'Ваш ранг был повышен до **{role.name.capitalize()}**!',
            #         color=role.color
            #     )
            # else:
            #     embed = discord.Embed(
            #         title='Повышение',
            #         description=f'Ваш уровень был повышен до **{out}**!',
            #         color=role.color
            #     )
            # await message.reply(embed=embed)

            if out <= len(LEVELS):
                role = message.guild.get_role(LEVELS[out-1])
                await message.author.add_roles(role)
            else:
                role = None
            
            image = bot.mg.render_prom(bot.mg.get_user(message.author.id), out, role) 
            file = discord.File(image, 'image.png')
            await message.reply(file=file)
            file.close()
            os.remove(image)


    # todo: giving roles upon member joining