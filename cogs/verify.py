import random
from discord.ext import commands
import discord
from log import *
from typing import *
from config import *
import utils
import datetime
import os


# setup
async def setup(bot: commands.Bot):

    @bot.hybrid_command(
        name='verify',
        aliases=['вериф', 'верифицировать', 'верифнуть'],
        description='Верифцироваться!'
    )
    async def slash_verify(ctx: commands.Context):
        '''
        Verify yourself.
        '''
        log(f'{ctx.author.id} requested verification')
        
        if ctx.channel.id != config.VERIFY_ID:
            return
        
        if ctx.author.get_role(config.VERIFY_ROLE):
            return
            
        user = bot.mg.get_user(ctx.author.id)
        if user.verifying:
            return

        user.verifying = True

        text = ''.join(random.choices('0123456789', k=5))
        image = bot.mg.render_captcha(text)
        file = discord.File(image, filename='captcha.png')

        embed = discord.Embed(
            title='Верификация',
            description='Введите **в чат** цифры с картинки.\n**На размышление даётся 60 секунд.**',
            color=DEFAULT_C
        )
        embed.set_image(url='attachment://captcha.png')

        msg = await ctx.reply(file=file, embed=embed)
        file.close()
        os.remove(image)

        # waiting for response
        try:
            message = await bot.wait_for(
                'message',
                check=lambda m: m.author.id == ctx.author.id and\
                    m.channel.id == ctx.channel.id,
                timeout=60
            )

        except:
            embed = discord.Embed(
                title='Верификация',
                description='Прошло больше 60 секунд.',
                color=ERROR_C
            )
            await msg.remove_attachments()
            await msg.edit(embed=embed)
            user.verifying = False
            return
        
        else:
            user.verifying = False
            await message.delete()
            await msg.remove_attachments()

            if text.lower() == message.content.lower():
                embed = discord.Embed(
                    title='Верификация',
                    description='Верификация прошла успешно!',
                    color=DEFAULT_C
                )
                await message.author.add_roles(
                    ctx.guild.get_role(config.VERIFY_ROLE)
                )

            else:
                embed = discord.Embed(
                    title='Верификация',
                    description='Верификация не пройдена.\n\nВы написали: '\
                        f'`{message.content}`\nНужно было написать: `{text}`\n\n'\
                        'Попробуйте ввести команду ещё раз.',
                    color=ERROR_C
                )

            await msg.edit(embed=embed)