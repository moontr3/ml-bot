from discord.ext import commands
import discord
from builder import *
from config import *
import utils
import api
from bot import MLBot

async def setup(bot: MLBot):
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
        
        # making select
        options = []

        for c, i in enumerate(bot.mg.data.get('faq', [])):
            options.append(discord.SelectOption(
                label=i['name'], value=str(c), emoji=i['emoji'],
                description=i['description']
            ))

        # view
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
        

    @bot.hybrid_command(
        name='faq-lite',
        aliases=['faqlite',"faq_lite",'fuckyou_lite','fuckyoulite','fuckyou-lite','помощьлайт','факюлайт','чаволайт'],
        description='Краткий список самых главных фич на сервере.'
    )
    @api.check_guild
    @discord.app_commands.guild_only()
    @discord.app_commands.guild_install()
    async def faq(ctx: commands.Context):
        options = []

        for c, i in enumerate(bot.mg.data.get('faq', [])):
            options.append(discord.SelectOption(
                label=i['name'], value=str(c), emoji=i['emoji'],
                description=i['description']
            ))

        preview = utils.get_faq_preview_view_items(bot.mg.data.get('quick_help', []))
        
        view = to_view(preview+[
            SEP(spacing=discord.SeparatorSpacing.large),
            'Если хочешь узнать о чем-либо в подробностях, ниже список всего, что у нас есть:',
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
        if interaction.type != discord.InteractionType.component:
            return
        
        # list of features
        if interaction.data['custom_id'] == 'quickhelp':
            options = []

            for c, i in enumerate(bot.mg.data.get('faq', [])):
                options.append(discord.SelectOption(
                    label=i['name'], value=str(c), emoji=i['emoji'],
                    description=i['description']
                ))

            preview = utils.get_faq_preview_view_items(bot.mg.data.get('quick_help', []))
            
            view = to_view(preview+[
                SEP(spacing=discord.SeparatorSpacing.large),
                'Если хочешь узнать о чем-либо в подробностях, ниже список всего, что у нас есть:',
                ui.Select(
                    custom_id='faq',
                    options=options,
                    placeholder='Выбери страничку...'
                )
            ])
            await interaction.response.send_message(view=view, ephemeral=True)


        # faq page from a select
        if interaction.data['custom_id'] == 'faq':
            index = int(interaction.data['values'][0])
            data = bot.mg.data.get('faq', [])[index]
            
            view = to_view(utils.get_faq_view_items(data))
            await interaction.response.send_message(view=view, ephemeral=True)


        # faq page by index
        if interaction.data['custom_id'].startswith('faq:'):
            index = int(interaction.data['custom_id'].split(':')[1])
            data = bot.mg.data.get('faq', [])[index]
            
            view = to_view(utils.get_faq_view_items(data))
            await interaction.response.send_message(view=view, ephemeral=True)