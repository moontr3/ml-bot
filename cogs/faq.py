from discord.ext import commands
import discord
from config import *

async def setup(bot: commands.Bot):
    question_list = bot.mg.data.get('faq', [])

    # command
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

        for c, i in enumerate(question_list):
            options.append(discord.SelectOption(label=i['name'], value=str(c)))

        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Select(
            custom_id='faq',
            options=options,
            placeholder='Выберите вопрос...'
        ))

        await ctx.reply(embed=embed, view=view)

    # handling components
    @bot.listen()
    async def on_interaction(interaction:discord.Interaction):
        if interaction.type == discord.InteractionType.component and interaction.data['custom_id'] == 'faq':
            index = int(interaction.data['values'][0])
            data = question_list[index]
            
            embed = discord.Embed(
                title=data['name'],
                description=data['contents'],
                color=DEFAULT_C
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)