from config import *
from discord.ext import commands


def predicate(ctx: commands.Context):
    if not ctx.guild:
        return False
    if ctx.guild.id != GUILD_ID:
        return False
    return True

check_guild = commands.check(predicate)
