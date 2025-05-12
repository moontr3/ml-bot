from discord.ext import commands
import discord
from config import *

async def setup(bot: commands.Bot):
    # command
    @bot.hybrid_command(
        name='faq',
        aliases=['чаво',"гайд",'guide','help','хелп','помощь'],
        description='Показывает часто задаваемые вопросы.'
    )
    @discord.app_commands.describe(
        page="Имя или сокращение желаемой страницы / вопроса."
    )
    async def faq(ctx: commands.Context, page: str = None):
        # page detected
        for i in bot.mg.data.get('faq', []):
            if any([item.lower() == page.lower() for item in i['alt']]):
                embed = discord.Embed(
                    title=i['name'],
                    description=i['contents'],
                    color=DEFAULT_C
                )
                await ctx.reply(embed=embed)
                return
        
        # no page
        embed = discord.Embed(
            title='Помощь',
            description='Приветствую в FAQ!\n\nЗдесь можно узнать больше о сервере и боте.',
            color=DEFAULT_C
        )

        options = []

        for c, i in enumerate(bot.mg.data.get('faq', [])):
            options.append(discord.SelectOption(
                label=i['name'], value=str(c), emoji=i['emoji']
            ))

        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Select(
            custom_id='faq',
            options=options,
            placeholder='Выбери вопрос...'
        ))

        await ctx.reply(embed=embed, view=view)

    # handling components
    @bot.listen()
    async def on_interaction(interaction:discord.Interaction):
        if interaction.type == discord.InteractionType.component and interaction.data['custom_id'] == 'faq':
            index = int(interaction.data['values'][0])
            data = bot.mg.data.get('faq', [])[index]
            
            embed = discord.Embed(
                title=data['name'],
                description=data['contents'],
                color=DEFAULT_C
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)