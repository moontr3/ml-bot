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

    @bot.hybrid_command(
        name='duel',
        aliases=['d','дуэль','д'],
        description='Сыграть с кем-то в дуэль.'
    )
    @discord.app_commands.user_install()
    @discord.app_commands.guild_install()
    @discord.app_commands.describe(user='Пользователь, с которым вы хотите играть.')
    async def slash_duel(ctx: commands.Context, user: discord.Member = None):
        log(f'{ctx.author.id} started duel')
        game = bot.mg.get_duel_by_user(ctx.author.id)

        if game:
            view = to_view(add_accessory(
                ['Вы уже играете в Дуэль!'],
                ui.Button(
                    style=discord.ButtonStyle.link,
                    label='Перейти', url=game.message.jump_url
                )
            ), ERROR_C)
            await ctx.reply(view=view, ephemeral=True)
            return
        
        if user and user.id == ctx.author.id:
            view = to_view('Интроверт ебаный.', ERROR_C)
            await ctx.reply(view=view, ephemeral=True)
            return
        
        if not user:
            view = to_view([
                f'### 🎯 Дуэль', SEP(),
                f'{ctx.author.name} хочет сыграть с кем-то в Дуэль!',
                [
                    ui.Button(
                        style=discord.ButtonStyle.blurple,
                        emoji='✋', label='Я хочу!', custom_id=f'acceptduel:{ctx.author.id}:0'
                    ),
                    ui.Button(
                        style=discord.ButtonStyle.red,
                        emoji=REJECT, label='Отменить', custom_id=f'giveupduel'
                    ),
                ]
            ])

        else:
            view = to_view([
                f'### 🎯 Дуэль', SEP(),
                f'{user.mention}, {ctx.author.name} хочет сыграть с тобой в Дуэль!',
                [
                    ui.Button(
                        style=discord.ButtonStyle.green,
                        emoji=ACCEPT, label='Го', custom_id=f'acceptduel:{ctx.author.id}:{user.id}'
                    ),
                    ui.Button(
                        style=discord.ButtonStyle.red,
                        emoji=REJECT, label='Не', custom_id=f'rejectduel:{ctx.author.id}:{user.id}'
                    ),
                ]
            ])

        game = bot.mg.add_duel(ctx.author.id)
        message = await ctx.reply(view=view)
        game.message = message


    @bot.listen()
    async def on_interaction(interaction:discord.Interaction):
        if interaction.type != discord.InteractionType.component:
            return
        
        cid = interaction.data['custom_id']

        # cancelling game
        if cid == 'giveupduel':
            game = bot.mg.give_up_duel(interaction.user.id)

            if not game:
                view = to_view('Вы сейчас не играете в Дуэль!', ERROR_C)
                await interaction.response.send_message(view=view, ephemeral=True)
                return
            
            if game.user2 is None:
                view = to_view([
                    f'### 🎯 Дуэль', SEP(),
                    f'<@{interaction.user.id}> отменил приглашение.'
                ], ERROR_C)
            else:
                view = to_view([
                    f'### 🎯 Дуэль', SEP(),
                    f'<@{interaction.user.id}> сдался...',
                ], ERROR_C)
            
            await interaction.response.edit_message(view=view)
            return
        
        # accepting invite
        if cid.startswith('acceptduel:'):
            user = int(cid.split(':')[1])
            target = int(cid.split(':')[2])

            if target != 0 and target != interaction.user.id:
                await interaction.response.send_message(view=c_to_view(NDTMKR_EMBED), ephemeral=True)
                return
            
            if interaction.user.id == user:
                view = to_view('С самим собой нельзя!', ERROR_C)
                await interaction.response.send_message(view=view, ephemeral=True)
                return
            
            game = bot.mg.start_duel(user, interaction.user.id)

            if not game:
                view = to_view('⚡ Игра - В С Ё', ERROR_C)
                await interaction.response.send_message(view=view, ephemeral=True)
                return
            
            if game.processing:
                view = to_view('Подожди, пока я дорасскажу.', ERROR_C)
                await interaction.response.send_message(view=view, ephemeral=True)
                return
            
            game.processing = True
            await interaction.response.defer()
            await game.start_seq()
            game.processing = False
        
        # rejecting invite
        if cid.startswith('rejectduel:'):
            user = int(cid.split(':')[1])
            target = int(cid.split(':')[2])

            if target != interaction.user.id and user != interaction.user.id:
                await interaction.response.send_message(view=c_to_view(NDTMKR_EMBED), ephemeral=True)
                return
            
            game = bot.mg.give_up_duel(user)

            if not game:
                view = to_view('⚡ Игра - В С Ё', ERROR_C)
                await interaction.response.send_message(view=view, ephemeral=True)
                return
            
            if game.processing:
                view = to_view('Подожди, пока я дорасскажу.', ERROR_C)
                await interaction.response.send_message(view=view, ephemeral=True)
                return
            
            view = to_view([
                f'### 🎯 Дуэль', SEP(),
                f'<@{interaction.user.id}> отменил приглашение.'
            ], ERROR_C)
            
            await interaction.response.edit_message(view=view)
            return
        
        # shooting
        if cid == 'duelshoot':
            game = bot.mg.get_duel_by_user(interaction.user.id)

            if not game:
                view = to_view('⚡ Игра - В С Ё', ERROR_C)
                await interaction.response.send_message(view=view, ephemeral=True)
                return
            
            if game.processing:
                view = to_view('Опоздал!', ERROR_C)
                await interaction.response.send_message(view=view, ephemeral=True)
                return
            
            game.processing = True
            await interaction.response.defer()
            await game.shoot(interaction.user.id)
            game.processing = False
        
        # focusing
        if cid == 'duelfocus':
            game = bot.mg.get_duel_by_user(interaction.user.id)

            if not game:
                view = to_view('⚡ Игра - В С Ё', ERROR_C)
                await interaction.response.send_message(view=view, ephemeral=True)
                return
            
            if game.processing:
                view = to_view('Опоздал!', ERROR_C)
                await interaction.response.send_message(view=view, ephemeral=True)
                return
            
            game.processing = True
            await interaction.response.defer()
            await game.act_focus(interaction.user.id)
            game.processing = False

