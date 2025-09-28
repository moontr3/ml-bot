import os
import random
import time
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


# setup
async def setup(bot: MLBot):
    
    async def send_to_logs(receiver: discord.User, amount: int, sender: discord.User):
        try:

            view = to_view(f'{sender.mention}   ›   {REP_EMOJIS[amount]}   ›   {receiver.mention}')

            await bot.webhook.send(view=view, username='Отправлен реп', avatar_url=JOIN_IMAGE, allowed_mentions=NO_MENTIONS)

        except Exception as e:
            log('Error sending rep to logs: ' + str(e), level=ERROR)

    
    @bot.listen('on_message')
    async def rep_earning(message: discord.Message):
        # filtering messages
        if message.author.bot: return

        # checking for rep command
        for command, amount in REP_COMMANDS.items():
            if message.content.lower() != command.lower():
                continue
            
            # checking message answer
            if message.reference == None:
                return

            try:
                reference = await message.channel.fetch_message(message.reference.message_id)
            except:
                return
            
            if reference.author == message.author:
                return

            # repblock
            botuser = bot.mg.get_user(message.author.id)
            if time.time() < botuser.rep_block_until:
                view = to_view([
                    '### У тебя репблок!', SEP(),
                    f'Ты сможешь репать <t:{int(botuser.rep_block_until)}:R>'
                ], ERROR_C)
                return await message.reply(view=view)

            # rep adding / removing
            if amount not in REP_EMOJIS: return
            emoji = REP_EMOJIS[amount]

            out = bot.mg.add_rep(reference.author.id, amount, message.author.id)

            if out != None:
                view = to_view([
                    '### Кулдаун!', SEP(), f'Попробуй снова <t:{int(out)}:R>'
                ], ERROR_C)
                return await message.reply(view=view)

            log(f'{reference.author.id} got {amount} rep from {message.author.id}')
            await send_to_logs(reference.author, amount, message.author)

            try:
                await reference.add_reaction(emoji)
            except:
                pass

            return
    

    @bot.listen('on_raw_reaction_add')
    async def rep_earning_reaction(reaction: discord.RawReactionActionEvent):
        # filtering rep reaction
        if reaction.emoji.id not in REP_EMOJI_IDS:
            return
        
        if reaction.guild_id != GUILD_ID:
            return
        
        if reaction.member.bot:
            return
        
        if reaction.channel_id not in CHATTABLE_CHANNELS:
            return
        
        # target message
        message = await bot.get_channel(reaction.channel_id).fetch_message(reaction.message_id)

        # repblock
        botuser = bot.mg.get_user(reaction.user_id)
        if time.time() < botuser.rep_block_until:
            view = to_view([
                '### У тебя репблок!', SEP(),
                f'Ты сможешь репать <t:{int(botuser.rep_block_until)}:R>'
            ], ERROR_C, text=f'<@{reaction.user_id}>')

            mentions = discord.AllowedMentions(replied_user=False)
            await message.reply(view=view, allowed_mentions=mentions)
            return
    
        # adding rep
        out = bot.mg.add_rep(message.author.id, REP_EMOJI_IDS[reaction.emoji.id], reaction.member.id)

        if out != None:
            view = to_view([
                '### Кулдаун!', SEP(), f'Попробуй снова <t:{int(out)}:R>'
            ], ERROR_C, text=f'<@{reaction.user_id}>')

            mentions = discord.AllowedMentions(replied_user=False)
            await message.reply(view=view, allowed_mentions=mentions)
            return

        await send_to_logs(message.author, REP_EMOJI_IDS[reaction.emoji.id], reaction.member)
        log(f'{message.author.id} got {REP_EMOJI_IDS[reaction.emoji.id]} rep from {reaction.member.id} (reaction)')
    

    @bot.hybrid_command(
        name='rep',
        description='Посмотреть репутацию.',
        aliases=['reputation','реп','репутация']
    )
    @api.check_guild
    @discord.app_commands.guild_only()
    @discord.app_commands.guild_install()
    @discord.app_commands.describe(
        user='Пользователь, репутацию которого вы хотите узнать.'
    )
    async def rep(ctx: commands.Context, user: discord.User = None):
        user = ctx.author if user == None else user

        if ctx.interaction:
            await ctx.interaction.response.defer()
        else:
            await ctx.channel.typing()

        # if user.bot:
        #     view = to_view('хахахаха боты сосите', ERROR_C)
        #     return await ctx.reply(view=view)

        path = bot.mg.renderer.rep(user)
        file = discord.File(path, 'image.png')
        await ctx.reply(file=file)

        file.close()
        os.remove(path)


    @bot.hybrid_command(
        name='repblock',
        aliases=['репблок','реп-блок','реп_блок','rep_block','rep-block'],
        description='👩‍⚖️ Запрещает участнику репать других на некоторое время.'
    )
    @api.check_guild
    @discord.app_commands.guild_only()
    @discord.app_commands.guild_install()
    @discord.app_commands.describe(
        member='Участник, которого нужно репблокнуть',
        time='Длина репблока в формате "10h", "3д" и так далее',
        reason='Причина'
    )
    async def slash_mute(
        ctx: commands.Context, member:discord.Member,
        time:str, *, reason:str=None
    ):
        '''
        Adds repblock to the specified user.
        '''
        # checking permissions
        if not ctx.permissions.moderate_members:
            await ctx.reply(view=c_to_view(MISSING_PERMS_EMBED))
            return

        # muting user
        data = utils.seconds_from_string(time)
        # checking input validity
        if data == None:
            await ctx.reply(view=c_to_view(INCORRECT_LENGTH_EMBED), ephemeral=True)
            return
        
        else:
            length = data[0]
            unit_name = data[1]
            unit_length = data[2]

        # repblocking user
        bot.mg.repblock(member.id, length)
        log(f'{ctx.author.id} repblocked user {member.id} for {time}')

        # sending message
        if reason == None:
            view = to_view([
                '### ➖ Репблок', SEP(),
                f'{member.mention} успешно репблокнут на **{unit_length} {unit_name}**.'
            ], DEFAULT_C)

        else:
            view = to_view([
                '### ➖ Репблок', SEP(),
                f'{member.mention} успешно репблокнут на **{unit_length} {unit_name}** '\
                    f'по причине **{utils.remove_md(reason)}**.'
            ], DEFAULT_C)
            
        await ctx.reply(view=view)