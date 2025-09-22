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
        self.mg = Manager(USERS_FILE, DATA_FILE, self.AI_KEY)
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

        for i in extensions:
            await self.unload_extension(i)
            log(f'Unloaded extension {i}')

        for i in glob.glob(f'{COGS_FOLDER}/*.py'):
            try:
                i = i.replace('\\','/')
                name = self.to_extension_name(i)
                await self.load_extension(name)
                log(f'Loaded extension {name}')

            except Exception as e:
                log(f'Extension unable to load: {e}', level=ERROR)


    # inbuilt commands
    @commands.command(aliases=['reloadcommands','reloadext','reloadextensions'])
    async def reload(self, ctx: commands.Context):
        '''
        Reloads cogs
        '''
        if ctx.author.id not in ADMINS: return

        log(f'{ctx.author.id} requested command reload')
        await self.load_commands()
        
        await ctx.reply(view=to_view('Команды перезагружены!', DEFAULT_C))


    @commands.command(aliases=['st'])
    async def synctree(self, ctx: commands.Context):
        '''
        Syncs slash command tree.
        '''
        if ctx.author.id not in ADMINS: return

        log(f'{ctx.author.id} requested tree syncing')
        view = to_view('Синхронизируем...', LOADING_C)
        msg = await ctx.reply(view=view)
        
        synced = await self.tree.sync()
        log(f'{ctx.author.id} synced tree with {len(synced)} commands', level=SUCCESS)
        view = to_view(f'{len(synced)} команд синхронизировано!', DEFAULT_C)
        await msg.edit(view=view)

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