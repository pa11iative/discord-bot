import os

from config import TOKEN
from loader import bot

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        try:
            bot.load_extension(f'cogs.{filename[:-3]}')
        except Exception as e:
            print(e)


if __name__ == '__main__':
    bot.run(TOKEN)