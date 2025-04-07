from discord.ext import commands
import discord
from config import *

async def setup(bot: commands.Bot):
    # faq things

    class CustomSelect(discord.ui.Select):
        async def callback(self, interaction:discord.Interaction):
            index = int(self.values[0])
            data = bot.mg.data.get('faq', [])[index]
            
            embed = discord.Embed(
                title=data['name'],
                description=data['contents'],
                color=DEFAULT_C
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)

    # command itself
    @bot.hybrid_command(
        name='faq',
        description='Показывает часто задаваемые вопросы.'
    )
    async def faq(ctx: commands.Context):
        embed = discord.Embed(
            title='Часто задаваемые вопросы',
            description='Выберете интересующий вопрос:',
            color=DEFAULT_C
        )

        options = []

        for c, i in enumerate(bot.mg.data.get('faq', [])):
            options.append(discord.SelectOption(label=i['name'], value=str(c)))

        view = discord.ui.View(timeout=None)
        view.add_item(CustomSelect(
            options=options,
            placeholder='Выберите вопрос...'
        ))

        await ctx.reply(embed=embed, view=view)