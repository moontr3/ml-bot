import asyncio
from copy import copy
import os
import aiohttp
from discord.ext import commands
import discord
import api
from log import *
from typing import *
from config import *
from aiogram import F, Router
from aiogram.utils import keyboard, formatting
import aiogram
from aiogram_media_group import media_group_handler
from PIL import Image
import io

import utils


# telegram bot

router = Router()
dcbot: commands.Bot = None
manager: api.Manager = None


async def on_router_message(messages: List[aiogram.types.Message]):
    bot = messages[0].bot
    chat_id = messages[0].chat.id
    content = '\n'.join([i.text or i.caption for i in messages if i.text or i.caption])
    clean_content = content
    photos = [i.photo[-1] for i in messages if i.photo]
    via = next((i.via_bot for i in messages if i.via_bot), None)
    show_caption_above = any([i.show_caption_above_media for i in messages])
    is_bot = any([i.from_user.is_bot for i in messages])
    user = messages[0].from_user

    # checking if channel in crossposting pairs
    for pair in manager.data['crosspost_pairs']:
        if pair["tg_id"] == chat_id:
            break
    else:
        return
    
    if is_bot and not pair['allow_bots']:
        return
    
    webhook = os.getenv(pair['webhook'])

    # sending message to discord channel
    try:
        view = ui.LayoutView()

        # user
        if pair['show_user'] and not webhook and not pair['footer']:
            if user.username:
                username = f'-# 👤 [{user.full_name}](<https://t.me/{user.username}>)'
            else:
                username = f'-# 👤 {user.full_name}'

            view.add_item(ui.TextDisplay(username))

        # reply text
        reply = next((i.reply_to_message for i in messages if i.reply_to_message), None)
        reply_text = ''

        if reply:
            data = manager.crossposter.get_dc_by_tg(chat_id, reply.message_id)

            if data:
                preview = data[1].replace(']', '\\]')
                url = data[2]

                if preview:
                    reply_text = f'[╭ {preview}](<{url}>)\n'

        # via
        if via and via.username:
            view.add_item(ui.TextDisplay(f'-# via [@{via.username}](<https://t.me/{via.username}>)'))

        # text (if set to show above media)
        if show_caption_above and len(content) > 0:
            view.add_item(ui.TextDisplay(content))

        # photos
        files = []

        if photos:
            gallery = ui.MediaGallery()

            log(f'Downloading {len(photos)} photos...')

            for i in photos:
                out = io.BytesIO()
                await bot.download(i.file_id, out)

                image = Image.open(copy(out))
                name = f'{i.file_unique_id}.{image.format.lower()}'

                files.append(discord.File(out, name))
                gallery.add_item(media='attachment://'+name)

            view.add_item(gallery)

        # text
        if not show_caption_above and len(content) > 0:
            if pair['show_user'] and webhook and not pair['footer'] and user.username:
                content += f'  [{VIEWUSER}](<https://t.me/{user.username}>)'

            view.add_item(ui.TextDisplay(reply_text + content))

        # button
        if pair['footer']:
            button = ui.Button(
                style=discord.ButtonStyle.link, label=messages[0].chat.title,
                url=pair["tg_link"] if pair["tg_link"] else messages[0].get_url()
            )

            if messages[0].author_signature:
                view.add_item(ui.Section(
                    ui.TextDisplay(f'-# {messages[0].author_signature}'),
                    accessory=button
                ))
            else:
                view.add_item(ui.ActionRow(button))

        # sending thru webhook
        if webhook:
            webhook = discord.Webhook.from_url(webhook, client=dcbot, bot_token=dcbot.TOKEN)

            user = messages[0].from_user if messages[0].from_user else messages[0].sender_chat
            name = utils.truncate(user.full_name, 32)
            avatar = TELEGRAM_IMAGE

            message = await webhook.send(
                view=view, username=name, avatar_url=avatar,
                files=files, allowed_mentions=ONLY_USERS, wait=True
            )

        # sending as bot
        else:
            channel: discord.TextChannel = dcbot.get_channel(pair["dc_id"])
            message = await channel.send(view=view, files=files, allowed_mentions=NO_MENTIONS)
        
        manager.crossposter.add_message(
            chat_id, message.id, [i.message_id for i in messages],
            utils.truncate(clean_content, 50), message.jump_url
        )

    except Exception as e:
        log(f'Unable to crosspost message: {e}', level=ERROR)


@router.channel_post(F.media_group_id.is_(None))
async def on_message(message: aiogram.types.Message):
    await on_router_message([message])


@router.message(F.media_group_id.is_(None))
async def on_message(message: aiogram.types.Message):
    await on_router_message([message])


@router.message(F.media_group_id.is_not(None))
@media_group_handler()
async def on_media_group(messages: List[aiogram.types.Message]):
    await on_router_message(messages)


# discord bot

async def setup(bot: commands.Bot):
    @bot.listen()
    async def on_message(message: discord.Message):
        if message.interaction_metadata:
            return
        
        # checking if channel in crossposting pairs
        for pair in bot.mg.data['crosspost_pairs']:
            if pair["dc_id"] == message.channel.id:
                break
        else:
            return
        
        if pair['users'] and message.author.id not in pair['users']:
            return
        
        if message.author.bot and not pair['allow_bots']:
            return
        
        # checking if its the same webhook
        if pair['webhook']:
            webhook = os.getenv(pair['webhook'])
            if webhook and webhook.split('/')[-2] == str(message.webhook_id):
                return
        
        # sending message to telegram
        try:
            tgbot: aiogram.Bot = bot.tgbot
            markup = None

            # link button
            if pair['footer']:
                button_text = f'🔗 {message.guild.name}'
                kb = keyboard.InlineKeyboardBuilder()
                kb.add(keyboard.InlineKeyboardButton(text=button_text, url=pair["dc_link"]))

                markup = kb.as_markup()

            # text
            clean_text = utils.discord_message_to_text(message)
            clean_text = formatting.Text(clean_text).as_markdown()

            if pair['show_user']:
                name = message.author.name.replace("_", "\\_")
                text = f'`{name}` 　 {clean_text}'
            else:
                text = clean_text

            # media
            media = []

            if len(message.attachments):
                for i in message.attachments:
                    caption = None
                    if len(media) == 0:
                        caption = text

                    if i.content_type.split('/')[0] == 'image':
                        item = aiogram.types.InputMediaPhoto(
                            media=i.url, caption=caption, parse_mode='MarkdownV2'
                        )
                    else:
                        continue

                    media.append(item)

            # reply
            reply_to = None

            if message.reference:
                # todo добавить превью в само сообщение если сообщение не найдено в базе
                messageid = bot.mg.crossposter.get_tg_by_dc(
                    message.reference.message_id
                )
                if messageid:
                    reply_to = messageid[1][0]

            # sending
            if media:
                new_message = await tgbot.send_media_group(
                    chat_id=pair["tg_id"], media=media, reply_to_message_id=reply_to
                )
                ids = [i.message_id for i in new_message]
            else:
                new_message = await tgbot.send_message(
                    chat_id=pair["tg_id"], text=text, parse_mode='MarkdownV2',
                    reply_markup=markup, reply_to_message_id=reply_to
                )
                ids = [new_message.message_id]

            bot.mg.crossposter.add_message(
                pair['tg_id'], message.id, ids, utils.truncate(clean_text, 50), message.jump_url
            )

        except Exception as e:
            log(f'Unable to crosspost message: {e}', level=ERROR)