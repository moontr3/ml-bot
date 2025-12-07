from typing import *
from config import *
import time
from log import *

# XP Leaderboard

class TimedLeaderboard:
    def __init__(self, data: dict = {}):
        '''
        Daily and weekly leaderboard.
        '''
        self.daily = data.get('daily', {})
        self.weekly = data.get('weekly', {})

        self.daily = {
            int(k): {int(k1): v1 for k1, v1 in v.items()}\
                for k, v in self.daily.items()
        }
        self.weekly = {
            int(k): {int(k1): v1 for k1, v1 in v.items()}\
                for k, v in self.weekly.items()
        }


    @property
    def current_day(self) -> int:
        return int(time.time()//86400)
    

    @property
    def current_week(self) -> int:
        return int(time.time()//604800)


    def check_leaderboard(self):
        if self.current_day not in self.daily:
            self.daily[self.current_day] = {}

        if self.current_week not in self.weekly:
            self.weekly[self.current_week] = {}


    def check_user(self, id:int):
        if id not in self.daily[self.current_day]:
            self.daily[self.current_day][id] = 0

        if id not in self.weekly[self.current_week]:
            self.weekly[self.current_week][id] = 0


    def add_xp(self, id:int, amount:int):
        '''
        Updates the leaderboard.
        '''
        self.check_leaderboard()
        self.check_user(id)

        self.daily[self.current_day][id] += amount
        self.weekly[self.current_week][id] += amount


    def get_daily_xp(self, id:int) -> int:
        self.check_leaderboard()

        if id not in self.daily[self.current_day]:
            return 0
        
        return self.daily[self.current_day][id]


    def get_weekly_xp(self, id:int) -> int:
        self.check_leaderboard()
        
        if id not in self.weekly[self.current_week]:
            return 0
        
        return self.weekly[self.current_week][id]


    def to_dict(self) -> dict:
        return {
            "daily": self.daily,
            "weekly": self.weekly
        }
