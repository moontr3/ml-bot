from discord.ext import commands
from discord import Webhook
import aiohttp
import discord
from log import *
from typing import *
from config import *

# setup
async def setup(bot: commands.Bot):
    @bot.listen()
    async def on_message_delete(message):
        session = aiohttp.ClientSession()
        webhook = Webhook.from_url(bot.WEBHOOK, session=session)
        embed = discord.Embed(title='Сообщение удалено', color=3092790)

        if len(message.content) > 1000:
            with open('temp/message.txt', 'w', encoding='utf-8') as f:
                f.write(message.content)
            file = [discord.File('temp/message.txt')]
        else:
            file = []
            embed.add_field(name='Сообщение', value=f'{message.content}', inline=False)

        embed.add_field(name='Участник', value=f'{message.author.mention} _({message.author} / {message.author.id})_', inline=True)
        embed.add_field(name='Канал', value=f'{message.channel.mention} _({message.channel.name} / {message.channel.id})_', inline=True)

        if message.attachments != []:
            embed.add_field(name='Вложения', value='\n'.join([i.url for i in message.attachments]), inline=False)

        await webhook.send(embed=embed, files=file)
        await session.close()


    @bot.listen()
    async def on_bulk_message_delete(messages):
        session = aiohttp.ClientSession()
        webhook = Webhook.from_url(config.webhook, session=session)
        embed = discord.Embed(title='Сообщения удалены', color=3092790)

        x = 0
        text = ''
        for i in range(len(messages)):
            msg = messages[x]
            text += f'{msg.author} ({msg.author.id}) >> {msg.channel} ({msg.channel.id}) / {msg.created_at}: {msg.content}\n'
            x += 1

        with open('temp/messages.txt', 'w', encoding='utf-8') as f:
            f.write(text)
        file = discord.File('temp/messages.txt')

        await webhook.send(embed=embed, file=file)
        await session.close()