import random
from typing import *
from config import *
from log import *
import time


# gambling


class GamblingPattern:
    def __init__(self, skin: str, pattern: List[int] = []):
        self.pattern: List[int] = pattern
        self.skin: str = skin


    @classmethod
    def random(cls, skin: str):
        pattern = [
            random.randint(1,8) for _ in range(9)
        ]
        return cls(skin, pattern)
    

    def get_column(self, index: str) -> List[int]:
        return self.pattern[index::3]
    

    def get_patterns(self) -> List[Tuple[List[int], int]]:
        out = []

        for i in GAMBLING_PATTERNS:
            items = [self.pattern[index] for index in i[0]]

            if items[1:] == items[:-1]:
                out.append(i)

        return out
    

    def get_xp(self) -> int:
        return sum([i[1] for i in self.get_patterns()])


# temp VC

class TempVC:
    def __init__(self, id: int, data: dict = {}):
        '''
        Temporary voice channel.
        '''
        self.id: int = id
        self.owner_id: int = data['owner_id']
        self.last_activity: float = data.get('last_activity', time.time())
        self.has_people: "bool | None" = None
        self.name: str = data['name']
        self.checked: bool = False # whether this vc was checked when updating activity
        self.created_at: float = data.get('created_at', time.time())

    
    def to_dict(self) -> dict:
        return {
            "owner_id": self.owner_id,
            "last_activity": self.last_activity,
            "name": self.name,
            "created_at": self.created_at
        }
    

# Q earning

class UnclaimedQ:
    def __init__(self, message_id: int):
        self.message_id: int = message_id
        self.spawned_at: float = time.time()
        self.claimed: List[int] = []


# mishkfrede

class MfrCard:
    def __init__(self, key: str, name: str, xp: int, image: str, color: str):
        self.key: str = key
        self.name: str = name
        self.xp: int = xp
        self.image: str = image
        self.color: str = color
