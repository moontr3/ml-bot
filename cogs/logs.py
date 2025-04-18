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

        elif message.content == '':
            return

        await webhook.send(embed=embed, files=file)
        await session.close()


    @bot.listen()
    async def on_bulk_message_delete(messages):
        session = aiohttp.ClientSession()
        webhook = Webhook.from_url(bot.WEBHOOK, session=session)
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
        

    # editing
    @bot.listen()
    async def on_message_edit(before, after):
        if before.content == after.content:
            return
        
        if not before.content:
            return
        
        session = aiohttp.ClientSession()
        webhook = Webhook.from_url(bot.WEBHOOK, session=session)
        embed = discord.Embed(title='Сообщение изменено', color=3092790)

        files = []
        if len(before.content) > 1000:
            with open('temp/before.txt', 'w', encoding='utf-8') as f:
                f.write(before.content)
            files.append(discord.File('temp/before.txt'))
        else:
            embed.add_field(name='Сообщение до изменений', value=f'{before.content}', inline=False)

        if len(after.content) > 1000:
            with open('temp/after.txt', 'w', encoding='utf-8') as f:
                f.write(after.content)
            files.append(discord.File('temp/after.txt'))
        else:
            embed.add_field(name='Сообщение после изменений', value=f'{after.content}', inline=False)

        embed.add_field(name='Участник', value=f'{before.author.mention} _({before.author} / {before.author.id})_', inline=True)
        embed.add_field(name='Канал', value=f'{before.channel.mention} _({before.channel.name} / {before.channel.id})_', inline=True)
        embed.add_field(name='Ссылка', value=f'{before.jump_url}', inline=False)

        if before.attachments != []:
            embed.add_field(name='Вложения до', value='\n'.join([i.url for i in before.attachments]), inline=False)
        if after.attachments != []:
            embed.add_field(name='Вложения после', value='\n'.join([i.url for i in after.attachments]), inline=False)

        await webhook.send(embed=embed, files=files)
        await session.close()


    # member joining
    @bot.listen()
    async def on_member_join(member):
        session = aiohttp.ClientSession()
        webhook = Webhook.from_url(bot.WEBHOOK, session=session)

        embed = discord.Embed(title='Участник присоединился к серверу', color=member.color)

        embed.add_field(name='Участник', value=f'{member.mention} _({member} / {member.id})_', inline=False)
        embed.set_thumbnail(url=member.avatar.url)

        await webhook.send(embed=embed)
        await session.close()


    # member leaving
    @bot.listen()
    async def on_member_remove(member):
        session = aiohttp.ClientSession()
        webhook = Webhook.from_url(bot.WEBHOOK, session=session)
        embed = discord.Embed(title='Участник вышел из сервера', color=member.color)

        embed.add_field(name='Участник', value=f'{member.mention} _({member} / {member.id})_', inline=False)
        embed.set_thumbnail(url=member.avatar.url)

        await webhook.send(embed=embed)
        await session.close()
