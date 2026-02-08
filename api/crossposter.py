from typing import *

from config import *
import json
import os
import time
from log import *


# crossposter message history


class CrossposterMessage:
    def __init__(self, dc_id: int, tg_ids: List[int], preview_text: str, dc_channel_id: int):
        self.dc_id = dc_id
        self.tg_ids = tg_ids
        self.preview_text = preview_text
        self.dc_channel_id = dc_channel_id


    def to_dict(self) -> list:
        return [
            self.dc_id,
            self.tg_ids,
            self.preview_text,
            self.dc_channel_id
        ]


    @classmethod
    def from_json(cls, data: dict):
        return cls(
            data[0],
            data[1],
            data[2],
            data[3],
        )


    @property
    def jump_url(self) -> str:
        return f'https://discord.com/channels/{GUILD_ID}/{self.dc_channel_id}/{self.dc_id}'


class Crossposter:
    def __init__(self, file: str):
        self.file: str = file
        self.last_commit: int = 0
        self.reload()


    def new(self):
        '''
        Rewrites the old database with the new one.
        '''
        self.messages: Dict[int, List[CrossposterMessage]] = {}
        self.commit()


    def panic(self):
        '''
        Creates a duplicate of the database and creates a new one.
        '''
        log('Panic in crossposter file!', 'api', WARNING)

        # copying file
        if os.path.exists(self.file):
            os.rename(self.file, self.file+'.bak')
            log(f'Cloned crossposter data file to {self.file}.bak', 'api')

        # creating a new one
        self.new()


    def reload(self):
        '''
        Reloads crossposter data.
        '''
        # user data
        try:
            with open(self.file, encoding='utf-8') as f:
                data = json.load(f)
        except:
            self.panic()
            return

        self.messages = {int(k): [
            CrossposterMessage.from_json(i) for i in v
        ] for k, v in data.get('messages', {}).items()}

        # saving
        self.commit()


    def commit(self):
        '''
        Saves data to the file.
        '''
        if time.time()-self.last_commit < 2:
            return
        self.last_commit = time.time()

        data = {
            "messages": {k: [i.to_dict() for i in v] for k, v in self.messages.items()}
        }

        # saving
        try:
            json_data = json.dumps(data, ensure_ascii=False)
        except Exception as e:
            log(f'Unable to save crossposter data: {e}', 'api', WARNING)
            return

        try:
            with open(self.file+'.temp', 'w', encoding='utf-8') as f:
                f.write(json_data)
                f.flush()
                os.fsync(f.fileno())

            os.replace(self.file+'.temp', self.file)
        except Exception as e:
            log(f'Unable to save crossposter data to file: {e}', 'api', ERROR)


    def add_message(
        self, chat_id: int, dc_id: int, tg_ids: List[int],
        preview_text: str, dc_channel_id: int
    ):
        '''
        Adds a pair of IDs to the database.
        '''
        if chat_id not in self.messages:
            self.messages[chat_id] = []

        self.messages[chat_id].append(CrossposterMessage(
            dc_id, tg_ids, preview_text, dc_channel_id
        ))

        if len(self.messages[chat_id]) > 500:
            self.messages[chat_id].pop(0)

        self.commit()


    def get_tg_by_dc(self, dc_id: int) -> CrossposterMessage:
        '''
        Get Telegram message ID by Discord message ID.
        '''
        for messages in self.messages.values():
            for message in messages:
                if message.dc_id == dc_id:
                    return message


    def get_dc_by_tg(self, chat_id: int, tg_id: int) -> CrossposterMessage:
        '''
        Get Discord message ID by Telegram message ID.
        '''
        return next((
            message for message in self.messages.get(chat_id, []) if tg_id in message.tg_ids),
        None)
