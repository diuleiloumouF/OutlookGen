import time
from contextlib import suppress
from random import choice, randint
from uuid import uuid4

from unique_names_generator import get_random_name
from unique_names_generator.data import ADJECTIVES, ANIMALS, COLORS, COUNTRIES, LANGUAGES, NAMES, STAR_WARS


class Utils:
    @staticmethod
    def replace(text: str, new: dict) -> str:
        for old, new in new.items():
            text = text.replace(old, new)
        return text

    @staticmethod
    def makeString(string_length=8):
        while True:
            rnd = str(uuid4())
            rnd = rnd.upper()
            rnd = rnd.replace("-", "")
            if not rnd[0:string_length][:1].isdigit():
                return rnd[0:string_length]

    @staticmethod
    def logger(email: str, password: str):
        open('accounts.txt', 'a+').write(f'{email}:{password}\n')

    def eGen(self):
        while True:
            try:
                # 生成基础名称
                base_name = get_random_name(
                    combo=[NAMES, choice([ADJECTIVES, ANIMALS, COLORS, LANGUAGES, NAMES])],
                    separator="").replace(" ", "")
                
                # 添加随机数字（可选）
                if randint(0, 1):
                    base_name += str(randint(0, 999))
                
                # 转换为小写并过滤掉非字母数字字符
                clean_name = ''.join(char.lower() for char in base_name if char.isalnum())
                
                # 确保名称不为空且不以数字开头
                if clean_name and not clean_name[0].isdigit():
                    return clean_name
            except:
                continue

    def randomize(self, string: str):
        # 生成只包含小写字母和数字的随机字符
        import string as str_module
        random_chars = str_module.ascii_lowercase + str_module.digits
        random_char = choice(random_chars)
        
        # 替换随机位置的字符
        if len(string) > 0:
            pos = randint(0, len(string) - 1)
            return string[:pos] + random_char + string[pos + 1:]
        return string


class Timer:
    def __init__(self):
        self.start_time = float
        self.now = float

    def start(self, t: time.time()):
        self.start_time = t

    def reset(self, t: time.time()):
        self.start_time = t

    def timer(self, t: time.time()):
        self.now = t - self.start_time
        return self.now
