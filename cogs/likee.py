import random
import discord
from discord.ext import commands
from config import *
import utils

async def setup(bot: commands.Bot):

    async def switch_answers(message: discord.Message, position: bool):
        user = bot.mg.get_user(message.author.id)
        word = 'Включил' if position else 'Выключил'
        if user.likee == position:
            embed = discord.Embed(
                color=ERROR_C,
                title='❌ ой всё',
                description=f'У тебя уже')
            embed.set_footer(text=message.author.name, icon_url=message.author.avatar.url if message.author.avatar is not None else None)
            await message.reply(embed=embed)
            return
        user.likee = position
        bot.mg.commit()
        embed = discord.Embed(
            color=DEFAULT_C,
            title='✅ бум',
            description=word)
        embed.set_footer(text=message.author.name, icon_url=message.author.avatar.url if message.author.avatar is not None else None)
        await message.reply(embed=embed)
        return
    

    async def query_answers(message: discord.Message):
        if random.random() < THRESHOLD:
            await message.reply(utils.get_likee())


    @bot.listen()
    async def on_message(message: discord.Message):
        if message.author.bot:
            return
        if message.guild == None:
            return
        if message.channel.id not in CHATTABLE_CHANNELS:
            return
        
        if message.content.lower() in {'-настройки лайки да', 'дабот настройки лайки да'}:
            await switch_answers(message, True)
        
        elif message.content.lower() in {'-настройки лайки нет', 'дабот настройки лайки нет'}:
            await switch_answers(message, False)
        
        elif bot.mg.get_user(message.author.id).likee:
            await query_answers(message)