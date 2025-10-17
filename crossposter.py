import random
import re
from typing import *

import aiogram
import api
from config import *
import utils
from aiogram.utils import formatting
from log import *


def get_preview_dc_message_text(message: discord.Message) -> str:
    clean_text = utils.discord_message_to_text(message)
    clean_text = utils.truncate(clean_text.replace('\n', ' '), 40)

    return clean_text
    

def get_preview_tg_message_text(content: str) -> str:
    clean_text = utils.truncate(content.replace('\n', ' '), 40)

    return clean_text


def get_dc_message_text(message: discord.Message, pair: Dict, manager: api.Manager = None) -> str:
    '''
    Returns message text.
    '''
    # text
    clean_text = utils.discord_message_to_text(message, manager)
    clean_text = formatting.Text(clean_text).as_markdown()

    if pair['show_user']:
        name = message.author.name.replace("_", "\\_")
        isbot = '🤖 ' if message.author.bot else ''
        text = f'{isbot}`{name}` 　 {clean_text}'
    else:
        text = clean_text

    return text


def get_tg_text(
    message: aiogram.types.Message,
    manager: api.Manager = None
):
    text = message.caption or message.text

    if not message.entities:
        return text
    
    # converting mention entities to user mentions
    offset = 0
    for i in message.entities:
        if i.type not in ['mention', 'text_mention']:
            continue

        startoffset = i.offset + offset
        endoffset = i.offset + i.length + offset

        # getting user
        if i.user:
            user = manager.get_user_by_tg(i.user.id)
        else:
            user = manager.get_user_by_tg_username(text[startoffset+1:endoffset])

        if not user:
            continue

        mention = f'<@{user.id}>'

        # replacing text
        text = text[0:startoffset] + mention + text[endoffset:]
        offset += len(mention) - i.length

    return text


def get_tg_message_view(
    messages: List[aiogram.types.Message],
    pair: Dict,
    webhook: str,
    manager: api.Manager,
    gallery: ui.MediaGallery,
    other_files: List[ui.File],
    skipped_files: int,
    sticker_gallery: ui.MediaGallery
) -> ui.LayoutView:
    '''
    Generates a Discord Components V2 view from a list of Telegram messages.
    '''
    view = ui.LayoutView()

    # variables
    chat_id = messages[0].chat.id
    user = messages[0].from_user
    content = '\n'.join([get_tg_text(i, manager) for i in messages if i.text or i.caption])
    content = utils.remove_md(content)
    user_name = user.full_name if not messages[0].sender_chat else messages[0].sender_chat.full_name
    add_text = len(content) > 0
    link = f'[{VIEWUSER}](<{messages[0].get_url()}>)'

    via = next((i.via_bot for i in messages if i.via_bot), None)
    show_caption_above = any([i.show_caption_above_media for i in messages])
    
    forward_data = next((
        i.forward_origin.sender_user if isinstance(i.forward_origin, aiogram.types.MessageOriginUser) else
        i.forward_origin.sender_chat if isinstance(i.forward_origin, aiogram.types.MessageOriginChat) else
        i.forward_origin.chat if isinstance(i.forward_origin, aiogram.types.MessageOriginChannel) else
        i.forward_origin.sender_user_name if isinstance(i.forward_origin, aiogram.types.MessageOriginHiddenUser)
        else None for i in messages if i.forward_origin
    ), None)

    forward_name = (
        forward_data if isinstance(forward_data, str) else
        forward_data.full_name if forward_data else None
    )
    forward_link = (
        None if isinstance(forward_data, str) else
        forward_data.username if forward_data and forward_data.username else None
    )

    # user
    if pair['show_user'] and not webhook and not pair['footer']:
        if user.username:
            username = f'-# 👤 [{user_name}](<https://t.me/{user.username}>)'
        else:
            username = f'-# 👤 {user_name}'

        view.add_item(ui.TextDisplay(username))

    # forwarded
    if forward_name:
        if forward_link:
            name = f'[{forward_name}](<https://t.me/{forward_link}>)'
        else:
            name = forward_name
        view.add_item(ui.TextDisplay(f'-# переслано от {name}'))

    # via
    if via and via.username:
        view.add_item(ui.TextDisplay(f'-# через [@{via.username}](<https://t.me/{via.username}>)'))

    # reply text
    reply = next((i.reply_to_message for i in messages if i.reply_to_message), None)
    reply_text = ''

    if reply:
        data = manager.crossposter.get_dc_by_tg(chat_id, reply.message_id)

        if data:
            preview = data.preview_text.replace(']', '\\]')
            preview = preview.replace('http://', '🔗 ').replace('https://', '🔗 ')
            url = data.jump_url

            if not preview:
                reply_text = f'[╭ _Нажмите, чтобы просмотреть вложение_](<{url}>)\n'
            else:
                reply_text = f'[╭ {preview}](<{url}>)\n'

    if reply_text and not add_text:
        view.add_item(ui.TextDisplay(reply_text))
    
    # gallery and files if shown above text
    if not show_caption_above: 
        if gallery:
            view.add_item(gallery)
        
        for i in other_files:
            view.add_item(i)

    # text
    if add_text:
        if pair['show_user'] and webhook and not pair['footer'] and user.username:
            content += f'  {link}'

        view.add_item(ui.TextDisplay(reply_text + content))

    # sticker
    if sticker_gallery == 'skipped':
        view.add_item(ui.TextDisplay(f'-# Анимированный стикер (не поддерживается)  {link}'))

    elif sticker_gallery:
        view.add_item(ui.TextDisplay(f'-# Стикер  {link}'))
        view.add_item(sticker_gallery)

    # gallery if shown below text
    if show_caption_above: 
        if gallery:
            view.add_item(gallery)
        
        for i in other_files:
            view.add_item(i)

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
    
    # empty view message
    if len(view.children) == 0:
        view.add_item(ui.TextDisplay(f'-# Пустое или неподдерживаемое сообщение  {link}'))

    # skipped files message
    if skipped_files > 0:
        view.add_item(ui.TextDisplay(f'-# Не отправлено несколько файлов ({skipped_files})  {link}'))

    return view