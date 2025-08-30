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
        name='manage-skin',
        aliases=['manageskin','manage_skin'],
        description='Изменить скины пользователя.'
    )
    async def slash_manage_skins(ctx:commands.Context, member:discord.User, action:Literal['set','add','remove'], skin:str):
        '''
        Changes user skins.
        '''
        if ctx.author.id not in ADMINS:
            await ctx.reply(view=c_to_view(NOT_ADMIN_EMBED), ephemeral=True)
            return

        log(f'{ctx.author.id} {action}s skins of {member.id}: {skin}')
        
        if action == 'set':
            if skin == 'none':
                skin = None
            bot.mg.set_skin(member.id, skin)
            desc = f'{member.mention} установлен скин **{skin}**'
        elif action == 'add':
            success = bot.mg.add_skin(member.id, skin)
            if success:
                desc = f'К {member.mention} добавлен скин **{skin}**'
            else:
                desc = f'АТАТА!!! ❌❌❌ у {member.mention} уже есть этот скин.'
        else:
            success = bot.mg.remove_skin(member.id, skin)
            if success:
                desc = f'У {member.mention} убран скин **{skin}**'
            else:
                desc = f'АТАТА!!! ❌❌❌ у {member.mention} не было этого скина.'

        view = to_view(desc)
        await ctx.reply(view=view)


    @bot.hybrid_command(
        name='skins',
        aliases=['скины'],
        description='Показывает список разблокированных скинов пользователя.'
    )
    @api.check_guild
    @discord.app_commands.guild_only()
    @discord.app_commands.guild_install()
    @discord.app_commands.describe(
        member='Участник сервера, у которого нужно узнать список скинов.'
    )
    async def slash_skins(ctx:discord.Interaction, member:discord.User=None):
        '''
        Shows user skins.
        '''
        if member == None:
            member = ctx.author

        log(f'{ctx.author.id} requested skin list of {member.id}')
        
        if ctx.interaction:
            await ctx.interaction.response.defer()
        else:
            await ctx.channel.typing()

        path = bot.mg.renderer.skin_list(member)
        file = discord.File(path, 'image.png')
        await ctx.reply(file=file)

        file.close()
        os.remove(path)


    @bot.hybrid_command(
        name='set-skin',
        aliases=['setskin','set_skin','установитьскин','установить_скин','установить-скин','поставить-скин','поставить_скин','поставитьскин'],
        description='Установить скин.'
    )
    @api.check_guild
    @discord.app_commands.guild_only()
    @discord.app_commands.guild_install()
    @discord.app_commands.describe(
        skin='Номер скина или его название.'
    )
    async def slash_setskin(ctx:discord.Interaction, *, skin:str):
        '''
        Sets a skin.
        '''
        log(f'{ctx.author.id} sets skin {skin}')
        
        if ctx.interaction:
            await ctx.interaction.response.defer()
        else:
            await ctx.channel.typing()

        skin = skin.lower().replace('ё','е')

        # choosing by key
        if skin in bot.mg.skins:
            pass
        # choosing by name
        elif skin in [i.name.lower() for i in bot.mg.skins.values()]:
            skin = [i for i in bot.mg.skins.values() if i.name.lower() == skin][0].key
        # choosing by index
        elif skin.isdigit():
            skin = int(skin)
            if skin > len(bot.mg.skins) or skin < 1:
                view = to_view('Такого скина нет.', ERROR_C)
                await ctx.reply(view=view, ephemeral=True)
                return
            
            skin = list(bot.mg.skins.values())[int(skin)-1].key
        # wrong input
        else:
            view = to_view('Такого скина нет.', ERROR_C)
            await ctx.reply(view=view, ephemeral=True)
            return
        
        # checking if user has skin
        user = bot.mg.get_user(ctx.author.id)

        if skin not in user.skins.items:
            view = to_view('У вас нет этого скина!', ERROR_C)
            await ctx.reply(view=view, ephemeral=True)
            return

        # selecting
        bot.mg.set_skin(ctx.author.id, skin)
        path = bot.mg.renderer.skin_set(user, skin)
        file = discord.File(path, 'image.png')
        await ctx.reply(file=file)

        file.close()
        os.remove(path)


    @bot.hybrid_command(
        name='remove-skin',
        aliases=['removeskin','remove_skin','убратьскин','убрать_скин','убрать-скин'],
        description='Убрать скин.'
    )
    @api.check_guild
    @discord.app_commands.guild_only()
    @discord.app_commands.guild_install()
    async def slash_removeskin(ctx:discord.Interaction):
        '''
        Removes a skin.
        '''
        log(f'{ctx.author.id} removes skin')

        # checking if user has any skin on
        user = bot.mg.get_user(ctx.author.id)

        if not user.skins._selected:
            view = to_view('У вас не установлен скин!', ERROR_C)
            await ctx.reply(view=view, ephemeral=True)
            return

        # removing
        skin = deepcopy(user.skins.selected)
        skin = bot.mg.skins[skin]
        bot.mg.set_skin(ctx.author.id, None)
        
        view = to_view(f'Вы убрали скин **{skin.name}**.', DEFAULT_C)
        await ctx.reply(view=view)


    @bot.command(name='spawnskin')
    async def cmd_spawnskin(ctx:commands.Context, skin:str=None):
        '''
        Spawns a skin.
        '''
        if ctx.author.id not in ADMINS: return
        if ctx.message.id in bot.mg.unclaimed: return
        
        skin: api.SkinData = bot.mg.get_random_skin()
        log(f'spawning manual skin {skin.key} in {ctx.channel.id} (msg {ctx.message.id})')

        await ctx.message.add_reaction(skin.emoji)
        bot.mg.unclaimed.append(ctx.message.id)


    @bot.listen()
    async def on_message(message:discord.Message):
        '''
        Spawning skin drops
        '''
        if message.channel.id not in CHATTABLE_CHANNELS: return
        if message.id in bot.mg.unclaimed: return
        if random.random() > SKIN_CHANCE: return

        # spawning skin
        skin: api.SkinData = bot.mg.get_random_skin()
        log(f'spawning skin {skin.key} in {message.channel.id} (msg {message.id})')

        await message.add_reaction(skin.emoji)
        bot.mg.unclaimed.append(message.id)


    @bot.listen()
    async def on_raw_reaction_add(reaction: discord.RawReactionActionEvent):
        '''
        Claiming gift drops
        '''
        if reaction.message_id not in bot.mg.unclaimed: return

        channel = bot.get_channel(reaction.channel_id)
        message = await channel.fetch_message(reaction.message_id)

        # checking if 30 mins have passed
        if time.time()-message.created_at.timestamp() > 60*30:
            return
        
        # getting skin
        skin = str(reaction.emoji.id)+'>'
        if skin not in [i.emoji.split(':')[2] for i in bot.mg.skins.values()]:
            return
        
        skin = reaction.emoji.name
        
        if reaction.message_id not in bot.mg.unclaimed: return

        log(f'{reaction.user_id} tries to collect skin {skin} in {reaction.channel_id}')

        # checking if user has this skin
        guild = bot.get_guild(reaction.guild_id)
        user = guild.get_member(reaction.user_id)
        out = bot.mg.add_skin(reaction.user_id, skin)

        if not out:
            log(f'{reaction.user_id} already has skin {skin}')
            return
        
        # success
        log(f'{reaction.user_id} collected skin {skin}')
        bot.mg.unclaimed.remove(reaction.message_id)

        await message.remove_reaction(reaction.emoji, user)

        image = bot.mg.renderer.skin_claim(user if user else reaction.user_id, skin)
        file = discord.File(image, filename='skin.png')
        mentions = discord.AllowedMentions(replied_user=False)

        await message.reply(f'<@{reaction.user_id}>', file=file, allowed_mentions=mentions)

        file.close()
        os.remove(image)