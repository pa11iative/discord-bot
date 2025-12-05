from disnake.ext import commands
from disnake import Intents
from config import server

bot = commands.Bot(command_prefix='!', intents=Intents.all(), test_guilds=[server])

bot.remove_command(name='help')