
from copy import copy
import os
import random
from discord.ext import commands
import discord
import api
from log import *
from typing import *
from config import *
from aiogram import F, Router
import aiogram
from aiogram_media_group import media_group_handler
from PIL import Image
import io

import crossposter
import utils


# telegram bot

router = Router()
dcbot: commands.Bot = None
manager: api.Manager = None


async def on_router_message(messages: List[aiogram.types.Message]):
    bot = messages[0].bot
    chat_id = messages[0].chat.id
    user = messages[0].from_user
    content = '\n'.join([i.text or i.caption for i in messages if i.text or i.caption])
    is_bot = any([i.from_user.is_bot for i in messages if i.from_user])
    is_forwarded = any([i.forward_date for i in messages])

    photos = [(i.photo[-1], i.has_media_spoiler) for i in messages if i.photo]
    documents = [i.document or i.audio or i.video for i in messages]
    documents = [i for i in documents if i]
    
    # getting name
    user_name = user.full_name if not messages[0].sender_chat else messages[0].sender_chat.full_name
    botuser = None

    if user:
        botuser = manager.get_user_by_tg(user.id)
        if botuser and botuser.display_name:
            user_name = botuser.display_name

    # checking if channel in crossposting pairs
    for pair in manager.data['crosspost_pairs']:
        if pair["tg_id"] == chat_id:
            break
    else:
        return
    
    if is_bot and not pair['allow_bots']:
        return
    
    webhook = os.getenv(pair['webhook'])

    # adding xp
    if botuser and pair['dc_id'] in CHATTABLE_CHANNELS and not is_forwarded:
        message = messages[0]
        botuser.minute_stats.update_minute()
        total_to_add = 0
        to_add = 0
            
        for i in messages:
            if i.reply_to_message:
                # adding 1 xp to author of replied message
                if not i.reply_to_message.from_user.is_bot:
                    author = manager.get_user_by_tg(i.reply_to_message.from_user.id)
                    if author:
                        manager.add_xp(author.id, REPLY_AUTHOR_XP, 'reply_tg')

                # adding xp for replying
                to_add += REPLY_XP
                break

        # xp for message
        if len(content) >= MIN_LENGTH_XP:
            to_add += BASE_XP_PER_MESSAGE
            to_add += len(content)//XP_PER_CHARACTERS
            to_add += len(photos)*XP_PER_ATTACHMENT
            to_add += len(documents)*XP_PER_ATTACHMENT

            total_to_add += min(to_add, MAX_XP_PER_MESSAGE)

        if MAX_MINUTE_XP-botuser.minute_stats.xp < total_to_add:
            total_to_add = MAX_MINUTE_XP-botuser.minute_stats.xp

        # xp for 00
        contains_zero = 'на часах 00' in content.lower()
        channel_matches = pair['dc_id'] == ZERO_ID
        message_time = message.date+datetime.timedelta(hours=3)
        time_matches = message_time.hour == 0 and message_time.minute == 0

        if contains_zero and channel_matches and time_matches:
            user_check = manager.check_user_zero(botuser.id)
            if user_check:
                total_to_add += random.randint(*ZERO_XP_RANGE)
            
        # adding xp
        botuser.minute_stats.add_xp(total_to_add)
        manager.add_xp(botuser.id, total_to_add, 'tg')

    # sending message to discord channel
    try:
        # photos
        files = []
        gallery = None
        skipped_files = 0

        if photos:
            gallery = ui.MediaGallery()

            log(f'Downloading {len(photos)} photos...')

            for i, is_spoiler in photos:
                if i.file_size > 8*1024*1024:
                    skipped_files += 1
                    log(f'Skipping photo {i.file_unique_id} because it is too big', level=WARNING)
                    continue

                out = io.BytesIO()
                await bot.download(i.file_id, out)

                image = Image.open(copy(out))
                name = f'{i.file_unique_id}.{image.format.lower()}'

                files.append(discord.File(out, name, spoiler=is_spoiler))
                gallery.add_item(media='attachment://'+files[-1].filename)

        # other files
        other_files = []

        if documents:
            log(f'Downloading {len(documents)} documents...')

            for i in documents:
                if i.file_size > 8*1024*1024:
                    skipped_files += 1
                    log(f'Skipping document {i.file_unique_id} because it is too big', level=WARNING)
                    continue

                out = io.BytesIO()
                await bot.download(i.file_id, out)
                filename = i.file_name if i.file_name else ''

                if len(filename.split('.')) > 1:
                    ext = '.'+filename.split('.')[-1]
                else:
                    ext = ''

                name = i.file_unique_id+ext

                files.append(discord.File(out, name))
                other_files.append(ui.File(media='attachment://'+name))

        # sticker
        sticker_gallery = None
        sticker = next((i.sticker for i in messages if i.sticker), None)

        if sticker and (sticker.is_animated or sticker.is_video):
            log(f'Skipping sticker {sticker.file_unique_id} because it is animated', level=WARNING)
            sticker_gallery = 'skipped'

        elif sticker:
            log(f'Downloading sticker...')

            out = io.BytesIO()
            await bot.download(sticker.file_id, out)

            image = Image.open(copy(out))
            name = f'{sticker.file_unique_id}.{image.format.lower()}'

            files.append(discord.File(out, name))
            sticker_gallery = ui.MediaGallery()
            sticker_gallery.add_item(media='attachment://'+files[-1].filename)

        # generating view
        view = crossposter.get_tg_message_view(
            messages, pair, webhook, manager, gallery, other_files, skipped_files, sticker_gallery
        )
        if len(view.children) == 0:
            view.add_item()
        
        saved_text = crossposter.get_preview_tg_message_text(content)

        # sending thru webhook
        if webhook:
            webhook = discord.Webhook.from_url(webhook, client=dcbot, bot_token=dcbot.TOKEN)

            user = messages[0].from_user if messages[0].from_user else messages[0].sender_chat
            name = utils.truncate(user_name, 32)
            
            # avatar
            avatar = TELEGRAM_IMAGE

            botuser = manager.get_user_by_tg(user.id)
            if botuser and botuser.avatar_url:
                avatar = botuser.avatar_url

            # sending
            message = await webhook.send(
                view=view, username=name, avatar_url=avatar,
                files=files, allowed_mentions=ONLY_USERS, wait=True
            )

        # sending as bot
        else:
            channel: discord.TextChannel = dcbot.get_channel(pair["dc_id"])
            message = await channel.send(view=view, files=files, allowed_mentions=ONLY_USERS) 
        
        manager.crossposter.add_message(
            chat_id, message.id, [i.message_id for i in messages],
            saved_text, message.channel.id
        )

    except Exception as e:
        log(f'Unable to crosspost message: {e}', level=ERROR)


# telegram

@router.channel_post(F.media_group_id.is_(None))
async def on_message(message: aiogram.types.Message):
    if message.from_user:
        manager.cache_tg_user_data(message.from_user)
    await on_router_message([message])

@router.channel_post(F.media_group_id.is_not(None))
@media_group_handler()
async def on_media_group(messages: List[aiogram.types.Message]):
    if messages[0].from_user:
        manager.cache_tg_user_data(messages[0].from_user)
    await on_router_message(messages)


@router.message(F.media_group_id.is_(None))
async def on_message(message: aiogram.types.Message):
    if message.from_user:
        manager.cache_tg_user_data(message.from_user)
    await on_router_message([message])

@router.message(F.media_group_id.is_not(None))
@media_group_handler()
async def on_media_group(messages: List[aiogram.types.Message]):
    if messages[0].from_user:
        manager.cache_tg_user_data(messages[0].from_user)
    await on_router_message(messages)
