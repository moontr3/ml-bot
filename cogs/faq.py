from discord.ext import commands
import discord
from builder import *
from config import *
import utils
import api

async def setup(bot: commands.Bot):
    # command
    @bot.hybrid_command(
        name='faq',
        aliases=['чаво',"гайд",'guide','help','хелп','помощь','fuckyou','факю','факью','fucku'],
        description='Показывает часто задаваемые вопросы.'
    )
    @api.check_guild
    @discord.app_commands.guild_only()
    @discord.app_commands.guild_install()
    @discord.app_commands.describe(
        page="Имя или сокращение желаемой страницы / вопроса."
    )
    async def faq(ctx: commands.Context, *, page: str = None):
        # page detected
        if page:
            for i in bot.mg.data.get('faq', []):
                if any([item.lower() == page.lower() for item in i['alt']]):
                    view = to_view(utils.get_faq_view_items(i))
                    await ctx.reply(view=view)
                    return
        
        # no page
        options = []

        for c, i in enumerate(bot.mg.data.get('faq', [])):
            options.append(discord.SelectOption(
                label=i['name'], value=str(c), emoji=i['emoji']
            ))

        view = to_view([
            '### 📚 Помощь', SEP(),
            'Приветствую в FAQ!', 'Здесь можно узнать больше о сервере и боте.', SEP(),
            ui.Select(
                custom_id='faq',
                options=options,
                placeholder='Выбери страничку...'
            )
        ])
        await ctx.reply(view=view)

    # handling components
    @bot.listen()
    async def on_interaction(interaction:discord.Interaction):
        if interaction.type == discord.InteractionType.component and interaction.data['custom_id'] == 'faq':
            index = int(interaction.data['values'][0])
            data = bot.mg.data.get('faq', [])[index]
            
            view = to_view(utils.get_faq_view_items(data))
            await interaction.response.send_message(view=view, ephemeral=True)