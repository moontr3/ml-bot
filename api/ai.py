from typing import *
from config import *
from log import *
import utils
import aiohttp
import base64


# ai


class AIMessage:
    def __init__(self, role: str, message: str, user: discord.User = None, attachment_url: list[str] = [], reply: discord.Message = None, reply_images: int = 0):
        self.role: str = role
        self.message: str = message
        self.user: discord.User = user
        self.attachment_url: list[str] = attachment_url
        self.reply: discord.Message = reply
        self.reply_images: int = reply_images


    def get_text(self, add_reply: bool = True) -> str:
        prefix = f'Отправил {self.user.display_name}: ' if self.user else ''
        
        if add_reply and self.reply and\
            len(self.reply.content) < 256 and len(self.reply.content) + self.reply_images > 0:
                prefix = f'*Ответ на "{utils.discord_message_to_text(self.reply)}" от '\
                    f'{self.reply.author.display_name}*\n'+prefix
            
        return prefix+self.message


    async def get_data(self, is_last: bool = False, add_reply: bool = True) -> dict:
        text = self.get_text(add_reply)

        if self.attachment_url and is_last:
            content = [{"type": "text", "text": text}]

            async with aiohttp.ClientSession() as session:
                for image in self.attachment_url:
                    async with session.get(image) as resp:
                        if resp.status != 200:
                            raise Exception(f"Failed to fetch image: {resp.status}")
                        
                        encoded_image = base64.b64encode(await resp.read()).decode('utf-8')
                        image_url = f"data:{resp.content_type};base64,{encoded_image}"
                        content.append({"type": "image_url", "image_url": {"url": image_url}})

            return content
        
        return text


class AIHistory:
    def __init__(self):
        self.history: List[AIMessage] = []


    def add(self, message: AIMessage):
        self.history.append(message)
        self.clean_up()


    def clean_up(self):
        new = []
        counter = 0

        for i in self.history[::-1]:
            textlen = len(i.get_text())
            counter += textlen

            # if it's not the 1st message and there's enough characters in history we stop
            if counter > MAX_CHARS_IN_HISTORY and counter > textlen:
                break

            counter += 50
            new.insert(0, i)

        self.history = new


    async def get_history(self) -> dict:
        data = [
            {"role": "system", "content": PROMPT}
        ]
        for index, i in enumerate(self.history):
            is_last = index == len(self.history)-1
            add_reply = index < len(self.history)-1
            data.append({"role": i.role, "content": await i.get_data(is_last, add_reply)})

        return data