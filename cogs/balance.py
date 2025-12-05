import disnake
from disnake.ext import commands
from utils.economy.balance import get_balance_embed
from utils.economy.transactions import deposit_money, withdraw_money, transfer_money
from utils.database import get_user_data

class BalanceCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="balance", description="Показать свой баланс")
    async def balance(self, inter: disnake.AppCmdInter, user: disnake.User = None):
        user = user or inter.author
        data = await get_user_data(user.id)
        embed = get_balance_embed(inter, user, data)
        await inter.response.send_message(embed=embed)

    @commands.slash_command(name="deposit", description="Положить деньги в банк")
    async def deposit(self, inter: disnake.AppCmdInter, amount: int):
        embed = await deposit_money(inter.author.id, amount)
        await inter.send(embed=embed)

    @commands.slash_command(name="withdraw", description="Снять деньги из банка")
    async def withdraw(self, inter: disnake.AppCmdInter, amount: int):
        embed = await withdraw_money(inter.author.id, amount)
        await inter.send(embed=embed)

    @commands.slash_command(name="pay", description="Перевести деньги другому пользователю")
    async def pay(self, inter: disnake.AppCmdInter, user: disnake.User, amount: int):
        embed = await transfer_money(inter.author, user, amount)
        await inter.send(embed=embed)

def setup(bot):
    bot.add_cog(BalanceCommands(bot))