import discord
from discord.ext import commands
from pydantic.dataclasses import dataclass
from aiogram import Bot

from api import *
from config import *
from utils import *
import os, glob, asyncio


@dataclass
class Features:
    ai: bool
    crossposter: bool

    def __repr__(self) -> str:
        return f'{self.ai=}, {self.crossposter=}'

    @classmethod
    def from_bot(cls, bot: "MLBot") -> 'Features':
        return cls(
            ai = bool(bot.AI_KEY),
            crossposter = bool(bot.tgbot)
        )


class MLBot(commands.Bot):
    def __init__(self, tg_bot: Bot | None = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.tgbot: Bot | None = tg_bot
        self.TOKEN: str = os.getenv('BOT_TOKEN')
        self.AI_KEY: str = os.getenv('AI_KEY')

        self.mg = Manager(USERS_FILE, DATA_FILE, self.AI_KEY, self)
        self.features: Features = Features.from_bot(self)
        log(f'Features: {self.features}')
        asyncio.run(self.load_commands())


    def to_extension_name(self, string:str) -> str:
        '''
        Converts relative path to filename without .py extension
        '''
        filename = string.removeprefix(f'{COGS_FOLDER}/').removesuffix('.py')
        return f'{COGS_FOLDER}.{filename}'
    

    async def load_commands(self) -> List[str]:
        '''
        Reloads all cogs.

        Returns a list of log entries.
        '''

        extensions = dict(self.extensions)
        success = 0
        total = 0

        for i in extensions:
            await self.unload_extension(i)
            log(f'Unloaded extension {i}')

        for i in glob.glob(f'{COGS_FOLDER}/*.py'):
            try:
                i = i.replace('\\','/')
                name = self.to_extension_name(i)
                await self.load_extension(name)
                # log(f'Loaded extension {name}')
                success += 1

            except Exception as e:
                log(f'Extension unable to load: {e}', level=ERROR)
            
            total += 1

        log(f'Loaded {success} / {total} extensions')


    # connection

    async def on_ready(self):
        WEBHOOK = os.getenv('LOGGING_WEBHOOK')
        self.webhook = discord.Webhook.from_url(WEBHOOK, client=self) if WEBHOOK else None

        SERVICE_WEBHOOK = os.getenv('SERVICE_WEBHOOK')
        self.service_webhook = discord.Webhook.from_url(SERVICE_WEBHOOK, client=self) if SERVICE_WEBHOOK else None
        
        log('Ready!', level=SUCCESS)


    async def on_disconnect(self):
        log('Disconnected', level=WARNING)

    async def on_connect(self):
        log('Connected')

    async def on_resumed(self):
        log('Resumed', level=SUCCESS)