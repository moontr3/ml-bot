import discord
from config import *
from bot import MLBot

async def setup(bot: MLBot):

    async def switch_answers(message: discord.Message, position: bool):
        user = bot.mg.get_user(message.author.id)
        word = 'включены' if position else 'выключены'
        if user.marked_by_beast == position:
            embed = discord.Embed(
                color=ERROR_C,
                title='❌ ой всё',
                description=f'У вас уже **{word}** ответки!'
            )
            embed.set_footer(text=message.author.name, icon_url=message.author.avatar.url if message.author.avatar is not None else None)
            await message.reply(embed=embed)
            return
        user.marked_by_beast = position
        bot.mg.commit()
        embed = discord.Embed(
            color=DEFAULT_C,
            title='✅ бум',
            description=f'Ответки теперь **{word}** для вас!'
        )
        embed.set_footer(text=message.author.name, icon_url=message.author.avatar.url if message.author.avatar is not None else None)
        await message.reply(embed=embed)
        return
    

    async def query_answers(message: discord.Message):
        answers: dict = bot.mg.data['legacy']
        answer = answers['equals'].get(message.content.lower())
        if answer is not None:
            await message.reply(answer)
            return
        for q, answer in answers['startswith'].items():
            if message.content.lower().startswith(q):
                await message.reply(answer)
                return


    @bot.listen()
    async def on_message(message: discord.Message):
        if message.author.bot:
            return
        if message.guild == None:
            return
        if message.channel.id not in CHATTABLE_CHANNELS:
            return
        
        if message.content.lower() in {'-настройки ответки да', 'дабот настройки ответки да'}:
            await switch_answers(message, True)
        
        elif message.content.lower() in {'-настройки ответки нет', 'дабот настройки ответки нет'}:
            await switch_answers(message, False)
        
        elif bot.mg.get_user(message.author.id).marked_by_beast:
            await query_answers(message)