import disnake
from disnake.ext import commands
from disnake import Embed
from utils.database import get_user_data, update_user_data
from utils.economy.loan import calculate_interest
from config import CURRENCY, EMBED_COLOR
from datetime import datetime, timedelta

class LoanCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="loan", description="Взять кредит")
    async def loan(self, inter: disnake.AppCmdInter, amount: int):
        if amount <= 0:
            return await inter.send("❌ Укажи сумму больше 0.", ephemeral=True)
        if amount > 10000:
            return await inter.send("❌ Сумма должна быть меньше 10000.", ephemeral=True)

        data = await get_user_data(inter.author.id)
        if data.get("debt", 0) > 0:
            return await inter.send("❌ Сначала погаси текущий долг.", ephemeral=True)

        total_debt, interest = calculate_interest(amount, 0.1)
        data["wallet"] += amount
        data["debt"] = total_debt
        data["debt_ts"] = datetime.now()
        await update_user_data(inter.author.id, data)

        embed = Embed(
            title="💰 Кредит оформлен",
            description=(
                f"Ты взял **{amount} {CURRENCY}** в кредит.\n"
                f"Проценты: **{interest} {CURRENCY}**\n"
                f"Общая сумма к возврату: **{total_debt} {CURRENCY}**\n"
                f"Погаси долг в течение 3 дней."
            ),
            color=EMBED_COLOR
        )
        await inter.send(embed=embed)

    @commands.slash_command(name="repay", description="Вернуть часть или весь кредит")
    async def repay(self, inter: disnake.AppCmdInter, amount: int):
        if amount <= 0:
            return await inter.send("❌ Укажи сумму больше 0.", ephemeral=True)

        data = await get_user_data(inter.author.id)
        if "debt" not in data or data["debt"] <= 0:
            return await inter.send("❌ У тебя нет долгов.", ephemeral=True)

        if data["wallet"] < amount:
            return await inter.send("❌ У тебя недостаточно средств.", ephemeral=True)

        repayment = min(amount, data["debt"])
        data["wallet"] -= repayment
        data["debt"] -= repayment

        if data["debt"] <= 0:
            data.pop("debt", None)
            data.pop("debt_ts", None)
            description = "✅ Ты полностью погасил долг."
        else:
            description = f"✅ Ты вернул **{repayment} {CURRENCY}**. Остаток долга: **{data['debt']} {CURRENCY}**."

        await update_user_data(inter.author.id, data)

        embed = Embed(
            title="✅ Погашение долга",
            description=description,
            color=EMBED_COLOR
        )
        await inter.send(embed=embed)

    @commands.slash_command(name="debt", description="Посмотреть долг и срок погашения")
    async def debt(self, inter: disnake.AppCmdInter):
        data = await get_user_data(inter.author.id)
        debt = data.get("debt", 0)
        if debt <= 0:
            return await inter.send("✅ У тебя нет долгов.", ephemeral=True)

        debt_ts = data.get("debt_ts")
        if isinstance(debt_ts, str):
            debt_ts = datetime.fromisoformat(debt_ts)

        deadline = debt_ts + timedelta(days=3)
        deadline_unix = int(deadline.timestamp())

        embed = Embed(
            title="📉 Информация о долге",
            description=(
                f"**Текущий долг:** {debt} {CURRENCY}\n"
                f"**Погаси до:** <t:{deadline_unix}:R>"
            ),
            color=EMBED_COLOR
        )
        await inter.send(embed=embed)


def setup(bot):
    bot.add_cog(LoanCog(bot))
