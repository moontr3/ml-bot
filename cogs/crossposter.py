
import os
import discord
from log import *
from typing import *
from config import *
from aiogram.utils import keyboard
import aiogram

import crossposter
from bot import MLBot


# setting up

async def setup(bot: MLBot):
    if not bot.features.crossposter:
        return
    
    # discord
    
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
        
        if pair['one_way']:
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
            if pair['footer'] and pair["dc_link"]:
                button_text = f'🔗 {message.guild.name}'
                kb = keyboard.InlineKeyboardBuilder()
                kb.add(keyboard.InlineKeyboardButton(text=button_text, url=pair["dc_link"]))

                markup = kb.as_markup()

            # text
            saved_text = crossposter.get_preview_dc_message_text(message)
            text = crossposter.get_dc_message_text(message, pair)

            # media
            media = []

            for i in message.attachments:
                caption = None
                if len(media) == 0:
                    caption = text

                if i.content_type.split('/')[0] == 'image':
                    item = aiogram.types.InputMediaPhoto(
                        media=i.url, caption=caption, parse_mode='MarkdownV2',
                        has_spoiler=i.is_spoiler()
                    )
                else:
                    item = aiogram.types.InputMediaDocument(
                        media=i.url, caption=caption, parse_mode='MarkdownV2',
                    )

                media.append(item)

            # stickers
            for i in message.stickers:
                caption = None
                if len(media) == 0:
                    caption = text

                item = aiogram.types.InputMediaPhoto(
                    media=i.url, caption=caption, parse_mode='MarkdownV2'
                )
                media.append(item)

            # reply
            reply_to = None

            if message.reference:
                messageid = bot.mg.crossposter.get_tg_by_dc(
                    message.reference.message_id
                )
                if messageid:
                    reply_to = messageid.tg_ids[0]

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
                pair['tg_id'], message.id, ids, saved_text, message.channel.id
            )

        except Exception as e:
            log(f'Unable to crosspost message: {e}', level=ERROR)