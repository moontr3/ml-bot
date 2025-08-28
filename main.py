from config import *
from api import *
from log import *

import discord
from discord.ext import commands
import glob
import asyncio
from dotenv import load_dotenv
import os
from typing import *

# loading token
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

bot = commands.Bot(command_prefix=PREFIXES, intents=discord.Intents.all(), help_command=None)
bot.mg = Manager(USERS_FILE, DATA_FILE)
bot.WEBHOOK = os.getenv('LOGGING_WEBHOOK')
bot.SERVICE_WEBHOOK = os.getenv('SERVICE_WEBHOOK')


# functions

def to_extension_name(string:str) -> str:
    '''
    Converts relative path to filename without .py extension
    '''
    filename = string.removeprefix(f'{COGS_FOLDER}/').removesuffix('.py')
    return f'{COGS_FOLDER}.{filename}'


async def load_commands() -> List[str]:
    '''
    Reloads all cogs.

    Returns a list of log entries.
    '''
    extensions = dict(bot.extensions)

    for i in extensions:
        await bot.unload_extension(i)
        log(f'Unloaded extension {i}')

    for i in glob.glob(f'{COGS_FOLDER}/*.py'):
        try:
            i = i.replace('\\','/')
            name = to_extension_name(i)
            await bot.load_extension(name)
            log(f'Loaded extension {name}')

        except Exception as e:
            log(f'Extension unable to load: {e}', level=ERROR)


# inbuilt commands
@bot.command(aliases=['reloadcommands','reloadext','reloadextensions'])
async def reload(ctx):
    '''
    Reloads cogs
    '''
    if ctx.author.id not in ADMINS: return

    log(f'{ctx.author.id} requested command reload')
    await load_commands()
    desc = f'{len(bot.commands)} commands, {len(bot.tree.get_commands())} slash, '\
        f'{len(bot.extensions)}/{len(glob.glob(f"{COGS_FOLDER}/*.py"))} cogs loaded'
    
    await ctx.reply(view=to_view('Команды перезагружены!', DEFAULT_C))


@bot.command(aliases=['st'])
async def synctree(ctx):
    '''
    Syncs slash command tree.
    '''
    if ctx.author.id not in ADMINS: return

    log(f'{ctx.author.id} requested tree syncing')
    view = to_view('Синхронизируем...', LOADING_C)
    msg = await ctx.reply(view=view)
    
    synced = await bot.tree.sync()
    log(f'{ctx.author.id} synced tree with {len(synced)} commands', level=SUCCESS)
    view = to_view(f'{len(synced)} команд синхронизировано!', DEFAULT_C)
    await msg.edit(view=view)
    

## RUNNING BOT

asyncio.run(load_commands())
bot.run(TOKEN)