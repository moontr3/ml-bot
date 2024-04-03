from typing import *
from config import *
import json
import os
from log import *
from copy import deepcopy



# user and user-related classes

class PollOption:
    def __init__(self, name:str, users:List[int]):
        '''
        Represents an option in a poll.
        '''
        self.name: str = name
        self.users: List[int] = users
        

class Poll:
    def __init__(self, data:dict):
        '''
        Represents a poll
        '''
        self.data: dict = data

        self.channel_id: int = data['channel_id']
        self.end_time: float = data['end_time']
        self.duration: float = data['duration']
        self.text: str = data['text']

        self.options: List[PollOption] = [
            PollOption(i, data['options'][i]) for i in data['options']
        ]

    def to_dict(self) -> dict:
        '''
        Converts the poll to a dict.
        '''
        return {
            'channel_id': self.channel_id,
            'end_time': self.end_time,
            'duration': self.duration,
            'text': self.text,
            'options': {i.name: i.users for i in self.options}
        }


class Reminder:
    def __init__(self, data:dict):
        '''
        Represents a reminder.
        '''
        self.message_id: int = data['id']
        self.channel_id: int = data['channel_id']
        self.end_time: float = data['end_time']
        self.duration: float = data['duration']
        self.text: str = data['text']
        self.jump_url: str = data['jump_url']

    def to_dict(self) -> dict:
        '''
        Converts the reminder to a dictionary.
        '''
        return {
            "id": self.message_id,
            "channel_id": self.channel_id,
            "end_time": self.end_time,
            "duration": self.duration,
            "text": self.text,
            "jump_url": self.jump_url
        }


class XP:
    def __init__(self, xp:int):
        '''
        User experience points, level, rank, etc.
        '''
        self.xp: int = xp
        self.reload_levels()


    def reload_levels(self):
        '''
        Reloads levels and percentages.
        '''
        xp = deepcopy(self.xp)
        xp_in_level = 1000
        level = 1
        while xp >= xp_in_level: 
            level += 1
            xp -= xp_in_level
            xp_in_level += 500

        self.level: int = level
        self.level_data: any = config.LEVELS[min(level, len(config.LEVELS))-1]
        self.level_xp: int = xp
        self.level_max_xp: int = xp_in_level
        self.level_percentage: float = xp/xp_in_level


class User:
    def __init__(self, id:int, data:dict={}):
        '''
        Represents a user.
        '''
        self.id: int = id

        self.hah: bool = data.get('hah', False)
        xp: int = data.get('xp', 0)
        self.xp = XP(xp)
        self.warns: int = data.get('warns', 0)
        self.quarantine: float | None = data.get('quarantine', None)
        self.polls: List[Poll] = [Poll(i) for i in data.get('polls', [])]
        self.reminders: List[Reminder] = [Reminder(i) for i in data.get('reminders', [])]
        self.tokens: Dict[int] = data.get('tokens', {})

        self.token_dig_timeout: float = data.get('token_dig_timeout', 0.0)
        self.games_timeout: float = data.get('games_timeout', 0.0)

    
    def to_dict(self) -> dict:
        '''
        Converts the class to a dictionary to store in the file.
        '''
        return {
            "xp": self.xp.xp,
            "hah": self.hah,
            "warns": self.warns,
            "quarantine": self.quarantine,
            "polls": [i.to_dict() for i in self.polls],
            "reminders": [i.to_dict() for i in self.reminders],
            "tokens": self.tokens,
            "token_dig_timeout": self.token_dig_timeout,
            "games_timeout": self.games_timeout
        }


# manager

class Manager:
    def __init__(self, users_file:str, data_file:str):
        '''
        API and backend manager.
        '''
        self.users_file: str = users_file
        self.data_file: str = data_file
        self.reload()


    def new(self):
        '''
        Rewrites the old database with the new one.
        '''
        self.users: Dict[int, User] = {}

        self.commit()


    def panic(self):
        '''
        Creates a duplicate of the database and creates a new one.
        '''
        log('Panic!', 'api', WARNING)

        # copying file
        if os.path.exists(self.users_file):
            os.rename(self.users_file, self.users_file+'.bak')
            log(f'Cloned user data file to {self.users_file}.bak', 'api')

        # creating a new one
        self.new()


    def reload(self):
        '''
        Reloads user data and bot data.
        '''
        # user data
        try:
            with open(self.users_file, encoding='utf-8') as f:
                data = json.load(f)
        except:
            self.panic()

        self.users = {int(id): User(int(id), data) for id, data in data['users'].items()}

        # saving
        self.commit()


    def commit(self):
        '''
        Saves user data to the file.
        '''
        data = {
            'users': {}    
        }

        # users
        for i in self.users:
            data['users'][i] = self.users[i].to_dict()

        # saving
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)


    def check_user(self, id:int):
        '''
        Checks if user exists in database. If not, creates one.
        '''
        if id in self.users:
            return
        
        self.users[id] = User(id)


    def get_user(self, id:int):
        '''
        Returns user by ID.
        '''
        self.check_user(id)
        return self.users[id]
