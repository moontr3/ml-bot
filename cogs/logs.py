from discord.ext import commands
from discord import Webhook
from bot import MLBot
import discord
from log import *
from typing import *
from config import *


# setup
async def setup(bot: MLBot):

    @bot.listen()
    async def on_message_delete(message: discord.Message):
        if not message.content and not message.attachments:
            return
        
        elements = [
            message.content if message.content else None,
            SEP(spacing=discord.SeparatorSpacing.large),
            f'{message.channel.mention} ・ {message.id}',
            f'{message.author.mention} ・ {message.author.id}'
        ]

        if message.attachments:
            elements.append(SEP())
            elements.append('### Вложения')
            elements.append('\n'.join(['- '+i.url for i in message.attachments]))

        view = to_view(elements)

        await bot.webhook.send(view=view, username='Сообщение удалено', avatar_url=DELETE_IMAGE, allowed_mentions=NO_MENTIONS)


    @bot.listen()
    async def on_bulk_message_delete(messages: List[discord.Message]):
        text = ''
        for msg in messages:
            text += f'[{msg.created_at}] {msg.author} ({msg.author.id}) >> {msg.channel} ({msg.channel.id}): {msg.content}\n'

        with open('temp/messages.txt', 'w', encoding='utf-8') as f:
            f.write(text)
        file = discord.File('temp/messages.txt')

        await bot.webhook.send(file=file, username=f'({len(messages)}) Сообщения удалены', avatar_url=DELETE_IMAGE)
        

    # editing
    @bot.listen()
    async def on_message_edit(before: discord.Message, after: discord.Message):
        if not before.content and not after.content and not before.attachments and not after.attachments:
            return
    
        elements = ['### До изменений', before.content if before.content else None]
        if before.attachments != []:
            elements.extend([SEP(), '\n'.join(['- '+i.url for i in before.attachments])])

        elements.extend([
            SEP(spacing=discord.SeparatorSpacing.large), '### После изменений',
            after.content if after.content else None
        ])
        if after.attachments != []:
            elements.extend([SEP(), '\n'.join(['- '+i.url for i in after.attachments])])

        elements.extend([
            SEP(spacing=discord.SeparatorSpacing.large),
            f'{after.channel.mention} ・ {after.channel.id}',
            f'{after.jump_url} ・ {after.id}',
            f'{after.author.mention} ・ {after.author.id}'
        ])

        view = to_view(elements)

        await bot.webhook.send(view=view, username='Сообщение изменено', avatar_url=EDIT_IMAGE, allowed_mentions=NO_MENTIONS)


    # member joining
    @bot.listen()
    async def on_member_join(member: discord.Member):
        elements = ['**'+member.name+'**', member.mention, str(member.id)]

        if member.avatar.url:
            elements = [add_accessory(elements, accessory=ui.Thumbnail(member.avatar.url))]
        
        view = to_view(elements)

        await bot.webhook.send(view=view, username='Участник зашел на сервер', avatar_url=JOIN_IMAGE)


    # member leaving
    @bot.listen()
    async def on_member_remove(member: discord.Member):
        elements = ['**'+member.name+'**', member.mention, str(member.id)]

        if member.avatar.url:
            elements = [add_accessory(elements, accessory=ui.Thumbnail(member.avatar.url))]
        
        view = to_view(elements)

        await bot.webhook.send(view=view, username='Участник вышел из сервера', avatar_url=LEAVE_IMAGE)
