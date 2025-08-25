import random
from discord.ext import commands
import discord
from config import *

ALLOWED = '0123456789d-+, '

async def setup(bot: commands.Bot):

    @bot.listen()
    async def on_message(message: discord.Message):
        if any(char not in ALLOWED for char in message.content.lower()):
            return
        
        # parsing
        dice = []
        bias = []

        text = message.content.lower().replace(',', '')
        while '  ' in text:
            text = text.replace('  ', ' ')
        text = text.split(' ')

        for element in text:
            # bias element
            if 'd' not in element:
                if element.startswith('-'):
                    bias.append(-int(element[1:]))
                elif element.startswith('+'):
                    bias.append(int(element[1:]))
                else:
                    return
                
                continue
                
            # dice element
            parts = element.split('d')

            if len(parts) != 2:
                return
            
            # how many dice to throw
            try: amount = int(parts[0])
            except: amount = 1
            
            if amount < 1:
                return
            
            # positive bias
            if '+' in parts[1]:
                try: bias.append(int(parts[1].split('+')[1]))
                except: return
                
                parts[1] = parts[1].split('+')[0]
            
            # negative bias
            if '-' in parts[1]:
                try: bias.append(-int(parts[1].split('-')[1]))
                except: return
                
                parts[1] = parts[1].split('-')[0]
            
            # dice
            try:
                for i in range(amount):
                    dice.append(int(parts[1]))
            except:
                return
            
        # checking data
        if len(dice) > 100:
            embed = discord.Embed(description=f'{len(dice)} кубиков чет многовато не думаешь', color=ERROR_C)
            await message.reply(embed=embed)
            return
        
        if sum(dice) > 1000000:
            embed = discord.Embed(description='пожалуй нет', color=ERROR_C)
            await message.reply(embed=embed)
            return
            
        # sending message
        results = [
            random.randint(1, i) for i in dice
        ]
        elements = results+bias
        total = sum(elements)
        text = ''

        if len(elements) > 1:
            text = '-# '
            for index, i in enumerate(elements):
                if index == 0:
                    text += str(i)
                else:
                    text += f' + {i}' if i > 0 else f' - {abs(i)}'
                     
            text += ' =\n'

        text += f'# {total}'

        await message.reply(text)