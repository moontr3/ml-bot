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
import datetime


# setup
async def setup(bot: commands.Bot):
    
    async def send_to_logs(receiver: discord.User, amount: int, sender: discord.User):
        try:
            session = aiohttp.ClientSession()
            webhook = discord.Webhook.from_url(bot.WEBHOOK, session=session)

            embed = discord.Embed(color=3092790)

            embed.add_field(name='Отправитель', value=sender.mention, inline=True)
            embed.add_field(name='Кол-во', value=REP_EMOJIS[amount], inline=True)
            embed.add_field(name='Получатель', value=receiver.mention, inline=True)

            await webhook.send(embed=embed, username='Отправлен реп', avatar_url=JOIN_IMAGE)
            await session.close()

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
                # embed = discord.Embed(
                #     description='Надо __ответить на сообщение__,', color=ERROR_C
                # )
                # return await message.reply(embed=embed)
                return

            try:
                reference = await message.channel.fetch_message(message.reference.message_id)
            except:
                return
            
            if reference.author == message.author:
                # embed = discord.Embed(
                #     description='Нельзя репать свои сообщения!', color=ERROR_C
                # )
                # return await message.reply(embed=embed)
                return

            if reference.author.bot: 
                # embed = discord.Embed(
                #     description='У ботов нет репутации!', color=ERROR_C
                # )
                # return await message.reply(embed=embed)
                return

            # repblock
            botuser = bot.mg.get_user(message.author.id)
            if time.time() < botuser.rep_block_until:
                embed = discord.Embed(
                    description=f'**У тебя репблок**! Ты сможешь репать <t:{int(botuser.rep_block_until)}:R>', 
                    color=ERROR_C
                )
                return await message.reply(embed=embed)

            # rep adding / removing
            if amount not in REP_EMOJIS: return
            emoji = REP_EMOJIS[amount]

            out = bot.mg.add_rep(reference.author.id, amount, message.author.id)

            if out != None:
                embed = discord.Embed(
                    description=f'**Кулдаун**! Попробуй снова <t:{int(out)}:R>', color=ERROR_C
                )
                return await message.reply(embed=embed)

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

        if message.author.bot or message.author.id == reaction.user_id:
            await message.remove_reaction(reaction.emoji, reaction.member)
            return

        # repblock
        botuser = bot.mg.get_user(reaction.user_id)
        if time.time() < botuser.rep_block_until:
            embed = discord.Embed(
                description=f'**У тебя репблок**! Ты сможешь репать <t:{int(botuser.rep_block_until)}:R>', 
                color=ERROR_C
            )
            mentions = discord.AllowedMentions(replied_user=False)
            await message.reply(f'<@{reaction.user_id}>', embed=embed, allowed_mentions=mentions)
            return
    
        # adding rep
        out = bot.mg.add_rep(message.author.id, REP_EMOJI_IDS[reaction.emoji.id], reaction.member.id)

        if out != None:
            embed = discord.Embed(
                description=f'**Кулдаун**! Попробуй снова <t:{int(out)}:R>', color=ERROR_C
            )
            mentions = discord.AllowedMentions(replied_user=False)
            await message.reply(f'<@{reaction.user_id}>', embed=embed, allowed_mentions=mentions)
            return

        await send_to_logs(message.author, REP_EMOJI_IDS[reaction.emoji.id], reaction.member)
        log(f'{message.author.id} got {REP_EMOJI_IDS[reaction.emoji.id]} rep from {reaction.member.id} (reaction)')
    

    @bot.hybrid_command(
        name='rep',
        description='Посмотреть репутацию.',
        aliases=['reputation','реп','репутация']
    )
    @discord.app_commands.guild_only()
    @discord.app_commands.describe(
        user='Пользователь, репутацию которого вы хотите узнать.'
    )
    async def rep(ctx: commands.Context, user: discord.User = None):
        user = ctx.author if user == None else user

        if ctx.interaction:
            await ctx.interaction.response.defer()
        else:
            await ctx.channel.typing()

        if user.bot:
            embed = discord.Embed(
                description='хахахаха боты сосите', color=ERROR_C
            )
            return await ctx.reply(embed=embed)

        path = bot.mg.renderer.rep(user)
        file = discord.File(path, 'image.png')
        await ctx.reply(file=file)

        file.close()
        os.remove(path)


    @bot.hybrid_command(
        name='repblock',
        aliases=['репблок','реп-блок','реп_блок','rep_block','rep-block'],
        description='Запрещает участнику репать других на некоторое время.'
    )
    @discord.app_commands.guild_only()
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
            await ctx.reply(embed=MISSING_PERMS_EMBED)
            return

        # muting user
        data = utils.seconds_from_string(time)
        # checking input validity
        if data == None:
            embed = discord.Embed(
                title='➖ Репблок', color=ERROR_C,
                description=f'Указана некорректная длина.'
            )
            await ctx.reply(embed=embed, ephemeral=True)
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
            embed = discord.Embed(
                title='➖ Репблок', color=DEFAULT_C,
                description=f'{member.mention} успешно репблокнут на **{unit_length} {unit_name}**.'
            )
        else:
            embed = discord.Embed(
                title='➖ Репблок', color=DEFAULT_C,
                description=f'{member.mention} успешно репблокнут на **{unit_length} {unit_name}**'\
                    f' по причине **{utils.remove_md(reason)}**.'
            )
        await ctx.reply(embed=embed)