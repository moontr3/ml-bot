import asyncio
import os
import random
import time
from discord.ext import commands
import discord
import api
from log import *
from typing import *
from config import *
import utils
from bot import MLBot
import datetime


def get_view(botuser: api.User, is_gif: bool = False, is_disabled: bool = False):
    return to_view([
        ui.MediaGallery(discord.MediaGalleryItem(
            f'attachment://image.{"gif" if is_gif else "png"}'
        )),
        ui.ActionRow(
            ui.Button(
                style=discord.ButtonStyle.primary,
                label='Потянуть рычаг' if not is_disabled else 'Крутим...',
                custom_id=f'spin:{botuser.id}{":g" if is_gif else ""}', disabled=is_disabled
            ),
            ui.Button(
                label=f'Вставить монетку ({botuser.q_level}/15)', emoji='🇶',
                custom_id=f'insert:{botuser.id}', disabled=botuser.q_level <= 0 or is_disabled
            )
        )
    ])


# setup
async def setup(bot: MLBot):
    
    @bot.hybrid_command(
        name='gambling',
        description='Лудомания слотмашина додеп',
        aliases=['гамблинг','гемблинг','слоты','слотмашина','лудомания','slots','slotmachine','sm','см']
    )
    @discord.app_commands.user_install()
    @discord.app_commands.guild_install()
    @discord.app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    async def slash_gambling(ctx: commands.Context):
        # command
        botuser: api.User = bot.mg.get_user(ctx.author.id)

        view = get_view(botuser)
        path = bot.mg.renderer.roulette.static(f'МОНЕТОК {botuser.coins:0>2}')
        file = discord.File(path, 'image.png')
        await ctx.reply(view=view, file=file)

        file.close()
        os.remove(path)


    # handling components
    @bot.listen()
    async def on_interaction(interaction:discord.Interaction):
        botuser: api.User = bot.mg.get_user(interaction.user.id)
        
        # inserting coin
        if interaction.data['custom_id'].startswith('insert:'):
            user = int(interaction.data['custom_id'].split(':')[1])

            if user != interaction.user.id:
                await interaction.response.send_message(view=c_to_view(NDTMKR_EMBED), ephemeral=True)
                return
            
            # taking q
            if not bot.mg.add_coin(botuser.id, 1):
                await interaction.response.send_message(
                    view=to_view([
                        f'### Не хватает Q!', SEP(),
                        f'У вас **{botuser.q_level}** / **15**. Посмотреть можно в `ml!bal`.'
                    ], ERROR_C), ephemeral=True
                )
                return

            # editing view
            view = get_view(botuser)
            path = bot.mg.renderer.roulette.static(f'МОНЕТОК {botuser.coins:0>2}')
            file = discord.File(path, 'image.png')

            await interaction.response.edit_message(view=view, attachments=[file])

            file.close()
            os.remove(path)

        # spinning roulette
        if interaction.data['custom_id'].startswith('spin:'):
            user = int(interaction.data['custom_id'].split(':')[1])

            if user != interaction.user.id:
                await interaction.response.send_message(view=c_to_view(NDTMKR_EMBED), ephemeral=True)
                return
            
            # editing viev
            view = get_view(
                botuser, len(interaction.data['custom_id'].split(':')) > 2,
                # if the amount of values on the button is more than 2
                # (spin:USERID:g), we put a gif in the view
                True
            )
            try:
                await interaction.response.edit_message(view=view)
            except Exception as e:
                log(f'Unable to edit message: {e}', level=ERROR)
                return

            # generating slots
            try:
                pattern = api.GamblingPattern.random('bebe')
                image, frames = bot.mg.renderer.roulette.gif(pattern)
                attachment = discord.File(image, 'image.gif')
            except Exception as e:
                log(f'Unable to generate gif: {e}', level=ERROR)
                return

            view = get_view(botuser, True, True)
            try:
                await interaction.edit_original_response(view=view, attachments=[attachment])
            except Exception as e:
                log(f'Unable to edit message: {e}', level=ERROR)
            attachment.close()
            os.remove(image)

            # waiting to edit message again
            await asyncio.sleep(frames*0.03+1)

            # editing message to show button again
            view = get_view(botuser, True)
            await interaction.edit_original_response(view=view)