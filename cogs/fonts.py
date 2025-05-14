import asyncio
from copy import deepcopy
import os
import random
import time
from discord.ext import commands
import discord
from log import *
from typing import *
from config import *
import api

import utils


# setup
async def setup(bot: commands.Bot):


    # @discord.app_commands.describe(
    #     member='Участник сервера, у которого нужно поменять опыт.',
    #     action='Действие',
    #     amount='Количество опыта'
    # )
    @bot.command(
        name='manage-font',
        aliases=['managefont','manage_font'],
        description='Изменить шрифты пользователя.'
    )
    async def slash_manage_fonts(ctx:commands.Context, member:discord.Member, action:Literal['set','add','remove'], font:str):
        '''
        Changes user fonts.
        '''
        if ctx.author.id not in ADMINS:
            embed = discord.Embed(
                description='Вы не администратор бота!',
                color=ERROR_C
            )
            await ctx.reply(embed=embed, ephemeral=True)
            return

        log(f'{ctx.author.id} {action}s fonts of {member.id}: {font}')
        
        if action == 'set':
            if font == 'none':
                font = None
            bot.mg.set_font(member.id, font)
            desc = f'{member.mention} установлен шрифт **{font}**'
            
        elif action == 'add':
            success = bot.mg.add_font(member.id, font)
            if success:
                desc = f'К {member.mention} добавлен шрифт **{font}**'
            else:
                desc = f'АТАТА!!! ❌❌❌ у {member.mention} уже есть этот шрифт.'

        else:
            success = bot.mg.remove_font(member.id, font)
            if success:
                desc = f'У {member.mention} убран шрифт **{font}**'
            else:
                desc = f'АТАТА!!! ❌❌❌ у {member.mention} не было этого шрифта.'

        embed = discord.Embed(
            description=desc, color=DEFAULT_C
        )
        await ctx.reply(embed=embed)


    @discord.app_commands.describe(
        member='Участник сервера, у которого нужно узнать список шрифтов.'
    )
    @bot.hybrid_command(
        name='fonts',
        aliases=['шрифты'],
        description='Показывает список разблокированных шрифтов пользователя.'
    )
    async def slash_fonts(ctx:discord.Interaction, member:discord.Member=None):
        '''
        Shows user fonts.
        '''
        if member == None:
            member = ctx.author

        log(f'{ctx.author.id} requested font list of {member.id}')
        
        if ctx.interaction:
            await ctx.interaction.response.defer()
        else:
            await ctx.channel.typing()

        path = bot.mg.render_font_list(member)
        file = discord.File(path, 'image.png')
        await ctx.reply(file=file)

        file.close()
        os.remove(path)


    @discord.app_commands.describe(
        font='Название шрифта.'
    )
    @bot.hybrid_command(
        name='set-font',
        aliases=['setfont','set_font','установитьшрифт','установить_шрифт','установить-шрифт'],
        description='Установить шрифт.'
    )
    async def slash_setfont(ctx:discord.Interaction, font:str):
        '''
        Sets a font.
        '''
        log(f'{ctx.author.id} sets font {font}')
        
        if ctx.interaction:
            await ctx.interaction.response.defer()
        else:
            await ctx.channel.typing()

        font = font.lower().replace('ё','е')

        # choosing by key
        if font in bot.mg.fonts:
            pass
        # choosing by name
        elif font in [i.name.lower() for i in bot.mg.fonts.values()]:
            font = [i for i in bot.mg.fonts.values() if i.name.lower() == font or font in i.alt][0].key
        # wrong input
        else:
            embed = discord.Embed(
                description='Такого шрифта нет.',
                color=ERROR_C
            )
            await ctx.reply(embed=embed, ephemeral=True)
            return
        
        # checking if user has font
        user = bot.mg.get_user(ctx.author.id)

        if font not in user.fonts.items:
            embed = discord.Embed(
                description='У вас нет этого шрифта!',
                color=ERROR_C
            )
            await ctx.reply(embed=embed, ephemeral=True)
            return

        # selecting
        bot.mg.set_font(ctx.author.id, font)
        path = bot.mg.render_font_set(font)
        file = discord.File(path, 'image.png')
        await ctx.reply(file=file)

        file.close()
        os.remove(path)


    @bot.hybrid_command(
        name='remove-font',
        aliases=['removefont','remove_font','убратьшрифт','убрать_шрифт','убрать-шрифт'],
        description='Убрать шрифт.'
    )
    async def slash_removefont(ctx:discord.Interaction):
        '''
        Removes a font.
        '''
        log(f'{ctx.author.id} removes font')

        # checking if user has any font on
        user = bot.mg.get_user(ctx.author.id)

        if not user.fonts._selected:
            embed = discord.Embed(
                description='У вас не установлен шрифт!',
                color=ERROR_C
            )
            await ctx.reply(embed=embed, ephemeral=True)
            return

        # removing
        font = deepcopy(user.fonts.selected)
        font = bot.mg.fonts[font]
        bot.mg.set_font(ctx.author.id, None)
        
        embed = discord.Embed(
            description=f'Вы убрали свой шрифт - **{font.name}**.',
            color=DEFAULT_C
        )
        await ctx.reply(embed=embed)


    @bot.command(name='spawnfont')
    async def cmd_spawnfont(ctx:commands.Context):
        '''
        Spawns a font.
        '''
        if ctx.author.id not in ADMINS: return
        if ctx.message.id in bot.mg.unclaimed: return
        
        font: api.FontData = bot.mg.get_random_font()
        log(f'spawning manual font {font.key} in {ctx.channel.id} (msg {ctx.message.id})')

        await ctx.message.add_reaction(font.emoji)
        bot.mg.unclaimed.append(ctx.message.id)


    @bot.listen()
    async def on_message(message:discord.Message):
        '''
        Spawning font drops
        '''
        if message.channel.id not in CHATTABLE_CHANNELS: return
        if message.id in bot.mg.unclaimed: return
        if random.random() > FONT_CHANCE: return

        # spawning skin
        font: api.FontData = bot.mg.get_random_font()
        log(f'spawning font {font.key} in {message.channel.id} (msg {message.id})')

        await message.add_reaction(font.emoji)
        bot.mg.unclaimed.append(message.id)


    @bot.listen()
    async def on_raw_reaction_add(reaction: discord.RawReactionActionEvent):
        '''
        Claiming font drops
        '''
        if reaction.message_id not in bot.mg.unclaimed: return

        channel = bot.get_channel(reaction.channel_id)
        message = await channel.fetch_message(reaction.message_id)

        # checking if 30 mins have passed
        if time.time()-message.created_at.timestamp() > 60*30:
            return
        
        # getting font
        font = str(reaction.emoji.id)+'>'
        if font not in [i.emoji.split(':')[2] for i in bot.mg.fonts.values()]:
            return
        
        font = reaction.emoji.name
        
        if reaction.message_id not in bot.mg.unclaimed: return

        log(f'{reaction.user_id} tries to collect font {font} in {reaction.channel_id}')

        # checking if user has this font
        guild = bot.get_guild(reaction.guild_id)
        user = guild.get_member(reaction.user_id)
        out = bot.mg.add_font(reaction.user_id, font)

        if not out:
            log(f'{reaction.user_id} already has font {font}')
            return
        
        # success
        log(f'{reaction.user_id} collected font {font}')
        bot.mg.unclaimed.remove(reaction.message_id)

        await message.remove_reaction(reaction.emoji, user)

        image = bot.mg.render_font_claim(user if user else reaction.user_id, font)
        file = discord.File(image, filename='font.png')
        await message.reply(file=file)

        file.close()
        os.remove(image)