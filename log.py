import colorama
import datetime
import config
colorama.init()

# levels
class Level:
    def __init__(self, name, color):
        self.name = name
        self.color = color

INFO =    Level("INFO   ", colorama.Fore.LIGHTBLUE_EX)
SUCCESS = Level("SUCCESS", colorama.Fore.LIGHTGREEN_EX)
WARNING = Level("WARNING", colorama.Fore.LIGHTYELLOW_EX)
ERROR =   Level("ERROR  ", colorama.Fore.LIGHTRED_EX)

# log
def log(text:str, origin:str='bot', level:Level=INFO, to_file:bool=True):
    '''
    Logs a message in the console and/or the file.
    '''
    ct = datetime.datetime.now()
    time = f'{ct.year}-{ct.month:0>2}-{ct.day:0>2} {ct.hour:0>2}:{ct.minute:0>2}:{ct.second:0>2}'

    # logging to console
    string = f'{level.color}[{level.name}]{colorama.Fore.RESET} [{time}] [{origin}] {text}'
    print(string)

    # logging to file
    if not to_file:
        return
    
    with open(config.LOG_FILE, 'a', encoding='utf-8') as file:
        string = f'[{level.name}] [{time}] [{origin}] {text}\n'
        file.write(string)