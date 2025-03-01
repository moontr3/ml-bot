from typing import *
from config import *
import datetime


# functions

def seconds_from_string(string:str) -> "Tuple[int,str,float|int] | None":
    '''
    Parses the string aka 10d, 3m and converts it to the
    amount of seconds.

    Returns None if unable to parse the string.

    Returns an integer as the amount of seconds,
    a string for the unit name and a float for the
    original provided amount.
    '''
    string = string.replace(' ','')
    
    amount = string[0:-1]
    try:
        amount = float(amount)
        if amount == int(amount):
            amount = int(amount)
    except:
        return None

    try:
        unit = UNITTABLE[string[-1]]
        unit_name = UNITNAMES[string[-1]]
    except:
        return None
    
    return int(amount*unit), unit_name, amount
    

def remove_md(string:str, escape_spoilers:bool=False) -> str:
    '''
    Escapes any markdown symbols.
    '''
    string = string.replace('\\', '\\\\') # confusing af 
    string = string.replace('*', '\\*')
    string = string.replace('_', '\\_')
    string = string.replace('~', '\\~')
    if escape_spoilers:
        string = string.replace('|', '\\|')

    return string

def datetime_to_text(time:datetime.datetime) -> str:
    '''
    Converts a datetime.datetime object into a neat string eg.

    11 Sep 2011, 14:22:16, Wed
    '''
    month = [
        'Янв','Фев','Мар','Апр','Май','Июн',
        'Июл','Авг','Сен','Окт','Ноя','Дек'
    ][time.month-1]
    weekday = [
        'Пн','Вт','Ср','Чт','Пт','Сб','Вс'
    ][time.weekday()]

    text = f'{time.day} {month} {time.year}, '\
        f'{time.hour}:{time.minute}:{time.second}'

    return