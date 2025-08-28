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
        mentions = discord.AllowedMentions(users=False, everyone=False, roles=False, replied_user=False)

        await webhook.send(view=view, username='Сообщение удалено', avatar_url=DELETE_IMAGE, allowed_mentions=mentions)
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
        session = aiohttp.ClientSession()
        webhook = Webhook.from_url(bot.WEBHOOK, session=session)
        
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
        mentions = discord.AllowedMentions(users=False, everyone=False, roles=False, replied_user=False)

        await webhook.send(view=view, username='Сообщение изменено', avatar_url=EDIT_IMAGE, allowed_mentions=mentions)
        await session.close()


    # member joining
    @bot.listen()
    async def on_member_join(member: discord.Member):
        session = aiohttp.ClientSession()
        webhook = Webhook.from_url(bot.WEBHOOK, session=session)

        view = ui.LayoutView()
        elements = [
            ui.TextDisplay('**'+member.name+'**'),
            ui.TextDisplay(member.mention),
            ui.TextDisplay(member.id),
        ]

        if member.avatar.url:
            elements = [ui.Section(*elements, accessory=ui.Thumbnail(member.avatar.url))]
        
        view.add_item(ui.Container(*elements))

        await webhook.send(view=view, username='Участник зашел на сервер', avatar_url=JOIN_IMAGE)
        await session.close()


    # member leaving
    @bot.listen()
    async def on_member_remove(member: discord.Member):
        session = aiohttp.ClientSession()
        webhook = Webhook.from_url(bot.WEBHOOK, session=session)

        view = ui.LayoutView()
        elements = [
            ui.TextDisplay('**'+member.name+'**'),
            ui.TextDisplay(member.mention),
            ui.TextDisplay(member.id),
        ]

        if member.avatar.url:
            elements = [ui.Section(*elements, accessory=ui.Thumbnail(member.avatar.url))]
        
        view.add_item(ui.Container(*elements))

        await webhook.send(view=view, username='Участник вышел из сервера', avatar_url=LEAVE_IMAGE)
        await session.close()
