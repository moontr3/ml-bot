import time
from discord.ext import commands
import discord
from log import *
from typing import *
from config import *
from bot import MLBot
import traceback

# setup
async def setup(bot: MLBot):
    # @bot.event
    # async def on_error(event, *args, **kwargs):
    #     '''Gets called when an unhandled exception is raised in a command.'''
    #     log(f'Unexpected error occured in {event}', level=ERROR)
    #     log(f'{len(args)} args:   {"; ".join([str(i) for i in args])}', level=ERROR)
    #     log(f'{len(kwargs)} kwargs: {"; ".join([f"{i}: {kwargs[i]}" for i in kwargs])}', level=ERROR)


    @bot.event
    async def on_command_error(ctx: commands.Context, error:Exception):
        '''Usually gets called when a user tries to incorrectly invoke a command.'''
        # not enough args
        if isinstance(error, commands.MissingRequiredArgument):
            log(f'{ctx.author} {ctx.author.id} missing required arguments', level=ERROR)
            await ctx.reply(view=c_to_view(ARGS_REQUIRED_EMBED))

        # missing required permissions
        elif isinstance(error, commands.MissingPermissions):
            log(f'{ctx.author} {ctx.author.id} missing permissions', level=ERROR)
            await ctx.reply(view=c_to_view(MISSING_PERMS_EMBED), ephemeral=True)

        # user not found
        elif isinstance(error, commands.UserNotFound) or isinstance(error, commands.MemberNotFound):
            log(f'{ctx.author} {ctx.author.id} user not found', level=ERROR)
            await ctx.reply(view=c_to_view(UNKNOWN_USER_EMBED), ephemeral=True)

        # channel not found
        elif isinstance(error, commands.ChannelNotFound):
            log(f'{ctx.author} {ctx.author.id} channel not found', level=ERROR)
            await ctx.reply(view=c_to_view(UNKNOWN_CHANNEL_EMBED))

        # not moonland
        elif isinstance(error, commands.CheckFailure):
            log(f'{ctx.author} {ctx.author.id} failed a check {error}', level=ERROR)
            await ctx.reply(view=c_to_view(NOT_MOONLAND_EMBED), ephemeral=True)

        # on cooldown
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.reply(view=to_view([
                '### Кулдаун!', SEP(), f'Попробуй ещё раз <t:{int(error.retry_after+time.time())}:R>'
            ], ERROR_C), ephemeral=True)

        # unknown command
        elif isinstance(error, commands.CommandNotFound):
            log(f'{ctx.author} {ctx.author.id} entered an unknown command: {ctx.message.content}', level=ERROR)

        # everything else basically
        else:
            log(f'{ctx.author} {ctx.author.id} issued a command error: {error}', level=ERROR)
            await ctx.reply(view=c_to_view(UNKNOWN_ERROR_EMBED), ephemeral=True)
            log('\n'.join(traceback.format_tb(error.__traceback__)), level=ERROR)
