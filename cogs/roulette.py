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
        name='russian-roulette',
        aliases=['rr','roulette','russian_roulette','russianroulette','рулетка','рр','русскаярулетка','русская-рулетка','русская_рулетка'],
        description='Сыграть с кем-то в русскую рулетку.'
    )
    @discord.app_commands.guild_only()
    @discord.app_commands.describe(user='Пользователь, с которым вы хотите играть.')
    async def slash_roulette(ctx: commands.Context, user: discord.Member = None):
        '''
        Shows bot ping.
        '''
        log(f'{ctx.author.id} started roulette')
        game = bot.mg.get_roulette_by_user(ctx.author.id)

        if game:
            view = to_view(add_accessory(
                ['Вы уже играете в русскую рулетку!'],
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
                f'### {GUN} Русская рулетка', SEP(),
                f'{ctx.author.name} хочет сыграть с кем-то в Русскую рулетку!',
                [
                    ui.Button(
                        style=discord.ButtonStyle.blurple,
                        emoji='✋', label='Я хочу!', custom_id=f'acceptroulette:{ctx.author.id}:0'
                    ),
                    ui.Button(
                        style=discord.ButtonStyle.red,
                        emoji=REJECT, label='Отменить', custom_id=f'giveuproulette'
                    ),
                ]
            ])

        else:
            view = to_view([
                f'### {GUN} Русская рулетка', SEP(),
                f'{user.mention}, {ctx.author.name} хочет сыграть с тобой в Русскую рулетку!',
                [
                    ui.Button(
                        style=discord.ButtonStyle.green,
                        emoji=ACCEPT, label='Го', custom_id=f'acceptroulette:{ctx.author.id}:{user.id}'
                    ),
                    ui.Button(
                        style=discord.ButtonStyle.red,
                        emoji=REJECT, label='Не', custom_id=f'rejectroulette:{ctx.author.id}:{user.id}'
                    ),
                ]
            ])

        game = bot.mg.add_roulette(ctx.author.id)
        message = await ctx.reply(view=view)
        game.message = message


    @bot.listen()
    async def on_interaction(interaction:discord.Interaction):
        if interaction.type != discord.InteractionType.component:
            return
        
        cid = interaction.data['custom_id']

        # cancelling game
        if cid == 'giveuproulette':
            game = bot.mg.give_up_roulette(interaction.user.id)

            if not game:
                view = to_view('Вы сейчас не играете в русскую рулетку!', ERROR_C)
                await interaction.response.send_message(view=view, ephemeral=True)
                return
            
            if game.user2 is None:
                view = to_view([
                    f'### {GUN} Русская рулетка', SEP(),
                    f'<@{interaction.user.id}> отменил приглашение.'
                ], ERROR_C)
            else:
                view = to_view([
                    f'### {GUN} Русская рулетка', SEP(),
                    f'<@{interaction.user.id}> сдался...',
                ], ERROR_C)
            
            await interaction.response.edit_message(view=view)
            return
        
        # accepting invite
        if cid.startswith('acceptroulette:'):
            user = int(cid.split(':')[1])
            target = int(cid.split(':')[2])

            if target != 0 and target != interaction.user.id:
                await interaction.response.send_message(view=c_to_view(NDTMKR_EMBED), ephemeral=True)
                return
            
            if interaction.user.id == user:
                view = to_view('С самим собой нельзя!', ERROR_C)
                await interaction.response.send_message(view=view, ephemeral=True)
                return
            
            game = bot.mg.start_roulette(user, interaction.user.id)

            if not game:
                view = to_view('⚡ Игра - В С Ё', ERROR_C)
                await interaction.response.send_message(view=view, ephemeral=True)
                return
            
            await interaction.response.defer()
            await game.start_seq()
        
        # rejecting invite
        if cid.startswith('rejectroulette:'):
            user = int(cid.split(':')[1])
            target = int(cid.split(':')[2])

            if target != interaction.user.id:
                await interaction.response.send_message(view=c_to_view(NDTMKR_EMBED), ephemeral=True)
                return
            
            game = bot.mg.give_up_roulette(user)

            if not game:
                view = to_view('⚡ Игра - В С Ё', ERROR_C)
                await interaction.response.send_message(view=view, ephemeral=True)
                return
            
            view = to_view([
                f'### {GUN} Русская рулетка', SEP(),
                f'<@{interaction.user.id}> отменил приглашение.'
            ], ERROR_C)
            
            await interaction.response.edit_message(view=view)
            return
        
        # shooting self
        if cid == 'rouletteself':
            game = bot.mg.get_roulette_by_user(interaction.user.id)

            if not game:
                view = to_view('⚡ Игра - В С Ё', ERROR_C)
                await interaction.response.send_message(view=view, ephemeral=True)
                return
            
            if interaction.user.id != game.player:
                await interaction.response.send_message(view=c_to_view(NDTMKR_EMBED), ephemeral=True)
                return
            
            await interaction.response.defer()
            await game.shoot_self()
        
        # shooting opponent
        if cid == 'rouletteother':
            game = bot.mg.get_roulette_by_user(interaction.user.id)

            if not game:
                view = to_view('⚡ Игра - В С Ё', ERROR_C)
                await interaction.response.send_message(view=view, ephemeral=True)
                return
            
            if interaction.user.id != game.player:
                await interaction.response.send_message(view=c_to_view(NDTMKR_EMBED), ephemeral=True)
                return
            
            await interaction.response.defer()
            await game.shoot_opponent()
