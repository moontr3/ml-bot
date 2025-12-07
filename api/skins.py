from typing import *
from config import *
import os
from log import *


# skin data

class SkinData:
    def __init__(self, key: str, data: dict = {}):
        '''
        Skin data.
        '''
        self.key: str = key
        self.name: str = data.get('name', None)
        self.emoji: str = data.get('emoji', None)
        self.rarity: int = data.get('rarity', None)

        # checking skin files
        for i in [
            'onelinerbg', 'prombg', 'xpbg', 'lbtopbg', 'lbmidbg', 'lbbottombg',
            'skintopbg', 'skinbottombg', 'badge', 'vcbg'
        ]:
            if not os.path.exists(f'assets/skins/{self.key}/{i}.png'):
                log(f'File {i} not found for skin {self.key}', 'api', WARNING)


class FontData:
    def __init__(self, key: str, data: dict = {}):
        '''
        Skin data.
        '''
        self.key: str = key
        self.name: str = data.get('name', None)
        self.emoji: str = data.get('emoji', None)
        self.rarity: int = data.get('rarity', None)
        self.alt: List[str] = data.get('alt', [])

        # checking skin files
        for i in [
            'bolditalic', 'bold', 'semibold', 'medium', 'regular'
        ]:
            if not os.path.exists(f'assets/fonts/{self.key}/{i}.ttf'):
                log(f'File {i} not found for font {self.key}', 'api', WARNING)