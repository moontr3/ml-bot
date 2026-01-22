import random
import discord
from typing import *
import pygame as pg
from log import *
from config import *
from .renderer import *
from .cbox import CBox
from .elements import *


class CCollection:
    def __init__(self, mg, bot):
        '''
        Collection of renderers.
        '''
        self.mg = mg
        self.bot = bot


    def user_xp(self, mg, user, is_tg: bool = True) -> str:
        '''
        Renders the XP embed for a discord user.
        '''
        r = Renderer((WIDTH, 100), (0,255,0))

        c = CBox([
            XPTitle(),
            14,
            XPElement(),
            14,
            XPLB(user, mg),
        ], user)
        c.render(r, is_tg)

        path = r.save('temp', 'png')
        return path