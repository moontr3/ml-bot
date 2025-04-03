from discord.ext import commands
import discord
from log import *
from typing import *
from config import *
import traceback

# setup
async def setup(bot: commands.Bot):
    # @bot.event
    # async def on_error(event, *args, **kwargs):
    #     '''Gets called when an unhandled exception is raised in a command.'''
    #     log(f'Unexpected error occured in {event}', level=ERROR)
    #     log(f'{len(args)} args:   {"; ".join([str(i) for i in args])}', level=ERROR)
    #     log(f'{len(kwargs)} kwargs: {"; ".join([f"{i}: {kwargs[i]}" for i in kwargs])}', level=ERROR)


    @bot.event
    async def on_command_error(ctx, error:Exception):
        '''Usually gets called when a user tries to incorrectly invoke a command.'''
        if isinstance(error, commands.MissingRequiredArgument):
            # not enough args
            log(f'{ctx.author} {ctx.author.id} missing required argument(s): {ctx.content}', level=ERROR)
            await ctx.reply(embed=ARGS_REQUIRED_EMBED)

        elif isinstance(error, commands.MissingPermissions):
            # missing required permissions
            log(f'{ctx.author} {ctx.author.id} missing permissions: {ctx.content}', level=ERROR)
            await ctx.reply(embed=MISSING_PERMS_EMBED)

        elif isinstance(error, commands.CommandNotFound):
            # unknown command
            log(f'{ctx.author} {ctx.author.id} entered an unknown command: {ctx.message.content}', level=ERROR)

        else:
            # everything else basically
            log(f'{ctx.author} {ctx.author.id} issued a command error: {error}', level=ERROR)
            await ctx.reply(embed=UNKNOWN_ERROR_EMBED)
            log('\n'.join(traceback.format_tb(error.__traceback__)), level=ERROR)
