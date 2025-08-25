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
    async def on_message_delete(message: discord.Message):
        session = aiohttp.ClientSession()
        webhook = Webhook.from_url(bot.WEBHOOK, session=session)
        embed = discord.Embed(
            color=3092790,
            description=f'{message.channel.mention} ・ {message.channel.id}'
        )

        embed.set_footer(
            text=f'{message.author.name} ・ {message.author.id}',
            icon_url=message.author.avatar.url if message.author.avatar is not None else None
        )

        if message.attachments != []:
            embed.add_field(name='Вложения', value='\n'.join([i.url for i in message.attachments]), inline=False)

        elif message.content == '':
            return

        await webhook.send(content=message.content, embed=embed, username='Сообщение удалено', avatar_url=DELETE_IMAGE)
        await session.close()


    @bot.listen()
    async def on_bulk_message_delete(messages: List[discord.Message]):
        session = aiohttp.ClientSession()
        webhook = Webhook.from_url(bot.WEBHOOK, session=session)

        text = ''
        for msg in messages:
            text += f'[{msg.created_at}] {msg.author} ({msg.author.id}) >> {msg.channel} ({msg.channel.id}): {msg.content}\n'

        with open('temp/messages.txt', 'w', encoding='utf-8') as f:
            f.write(text)
        file = discord.File('temp/messages.txt')

        await webhook.send(file=file, username=f'({len(messages)}) Сообщения удалены', avatar_url=DELETE_IMAGE)
        await session.close()
        

    # editing
    @bot.listen()
    async def on_message_edit(before: discord.Message, after: discord.Message):
        if before.content == after.content:
            return
        
        if not before.content:
            return
        
        session = aiohttp.ClientSession()
        webhook = Webhook.from_url(bot.WEBHOOK, session=session)
        
        # embed
        embed = discord.Embed(
            color=3092790,
            description=f'{after.channel.mention} ・ {after.channel.id}\n{after.jump_url} ・ {after.id}'
        )
        embed.set_footer(
            text=f'{after.author.name} ・ {after.author.id}',
            icon_url=after.author.avatar.url if after.author.avatar is not None else None
        )

        # embeds before and after
        before_embed = discord.Embed(title='До изменений', color=3092790, description=before.content)
        after_embed = discord.Embed(title='После изменений', color=3092790, description=after.content)

        if before.attachments != []:
            before_embed.add_field(name='Вложения', value='\n'.join([i.url for i in before.attachments]), inline=False)
        if after.attachments != []:
            after_embed.add_field(name='Вложения', value='\n'.join([i.url for i in after.attachments]), inline=False)

        embeds = [before_embed, after_embed, embed]

        await webhook.send(embeds=embeds, username='Сообщение изменено', avatar_url=EDIT_IMAGE)
        await session.close()


    # member joining
    @bot.listen()
    async def on_member_join(member: discord.Member):
        session = aiohttp.ClientSession()
        webhook = Webhook.from_url(bot.WEBHOOK, session=session)

        embed = discord.Embed(title=member.name, color=3092790, description=f'{member.mention} ・ {member.id}')
        embed.set_thumbnail(url=member.avatar.url if member.avatar is not None else None)

        await webhook.send(embed=embed, username='Участник зашел на сервер', avatar_url=JOIN_IMAGE)
        await session.close()


    # member leaving
    @bot.listen()
    async def on_member_remove(member: discord.Member):
        session = aiohttp.ClientSession()
        webhook = Webhook.from_url(bot.WEBHOOK, session=session)

        embed = discord.Embed(title=member.name, color=3092790, description=f'{member.mention} ・ {member.id}')
        embed.set_thumbnail(url=member.avatar.url if member.avatar is not None else None)

        await webhook.send(embed=embed, username='Участник вышел из сервера', avatar_url=LEAVE_IMAGE)
        await session.close()
