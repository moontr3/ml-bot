import os
import random
from discord.ext import commands
import discord
from log import *
from typing import *
from config import *
import api
from PIL import Image, ImageDraw, ImageFont


def regen_bar(id, percentage: float, color=(252,186,0), bg_color=(20,21,23), size=(1000, 50)):
    image = Image.new('RGB', (size[0], size[1]), bg_color)
    
    # drawing bar
    draw = ImageDraw.Draw(image)
    draw.line([(0,size[1]//2), (percentage*size[0],size[1]//2)], fill=color, width=size[1]+2)

    # saving
    image.save(f'temp\\{id}.png')
    image.close()


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

    # xp command
    @discord.app_commands.describe(
        member='Участник сервера, у которого нужно узнать опыт.'
    )
    @bot.hybrid_command(
        name='xp',
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

        desc = f'### {role.name.title()} ・ Уровень {acc.xp.level} ・ {acc.xp.xp} XP'\
            f'\n**{acc.xp.level_xp}** / **{acc.xp.level_max_xp}** (**{int(acc.xp.level_percentage*100)}%**)'

        embed = discord.Embed(
            description=desc, color=role.color
        )
        embed.set_author(name=f'✨ Опыт {member.display_name}')
        embed.set_image(url='attachment://image.png')

        if ctx.channel.id not in CHATTABLE_CHANNELS:
            embed.set_footer(text='⚠ В этом канале нельзя получать опыт!')

        bar = regen_bar(member.id, acc.xp.level_xp/acc.xp.level_max_xp)
        file = discord.File(f'temp/{member.id}.png', 'image.png')
        await ctx.reply(embed=embed, file=file)

        file.close()
        os.remove(f'temp/{member.id}.png')


    # gaining xp
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
            

    # todo: giving roles upon member joining