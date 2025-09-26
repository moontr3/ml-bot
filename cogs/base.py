from discord.ext import commands
from discord import Webhook
import aiohttp
import discord
from log import *
from typing import *
from config import *
from bot import MLBot


# setup
async def setup(bot: MLBot):

    # inbuilt commands
    @bot.command(aliases=['reloadcommands','reloadext','reloadextensions'])
    async def reload(ctx: commands.Context):
        '''
        Reloads cogs
        '''
        if ctx.author.id not in ADMINS: return

        log(f'{ctx.author.id} requested command reload')
        await bot.mg.load_commands()
        
        await ctx.reply(view=to_view('Команды перезагружены!', DEFAULT_C))


    @bot.command(aliases=['st'])
    async def synctree(ctx: commands.Context):
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