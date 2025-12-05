import disnake
from disnake.ext import commands
from utils.database import get_user_data, update_user_data
from utils.economy.rewards import can_claim_reward, get_reward_amount, format_timestamp
from config import CURRENCY
from datetime import datetime

class RewardCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="daily", description="Получить ежедневную награду")
    async def daily(self, inter: disnake.AppCmdInter):
        data = await get_user_data(inter.author.id)
        can_claim, wait = can_claim_reward(data, "daily_ts", 86400)

        if not can_claim:
            embed = disnake.Embed(
                description=f"⏳ Ты уже получал ежедневную награду. Приходи снова <t:{format_timestamp(wait)}:R>.",
                color=disnake.Color.orange()
            )
            await inter.send(embed=embed, ephemeral=True)
            return

        reward = get_reward_amount("daily")
        data["wallet"] += reward
        data["daily_ts"] = datetime.now()
        await update_user_data(inter.author.id, data)

        embed = disnake.Embed(
            title="📅 Ежедневная награда",
            description=f"Ты получил **{reward} {CURRENCY}**. Приходи завтра!",
            color=disnake.Color.green()
        )
        await inter.send(embed=embed)

    @commands.slash_command(name="weekly", description="Получить еженедельную награду")
    async def weekly(self, inter: disnake.AppCmdInter):
        data = await get_user_data(inter.author.id)
        can_claim, wait = can_claim_reward(data, "weekly_ts", 604800)

        if not can_claim:
            embed = disnake.Embed(
                description=f"⏳ Ты уже получал еженедельную награду. Приходи снова <t:{format_timestamp(wait)}:R>.",
                color=disnake.Color.orange()
            )
            await inter.send(embed=embed, ephemeral=True)
            return

        reward = get_reward_amount("weekly")
        data["wallet"] += reward
        data["weekly_ts"] = datetime.now()
        await update_user_data(inter.author.id, data)

        embed = disnake.Embed(
            title="📆 Еженедельная награда",
            description=f"Ты получил **{reward} {CURRENCY}**. Приходи через неделю!",
            color=disnake.Color.blue()
        )
        await inter.send(embed=embed)

    @commands.slash_command(name="monthly", description="Получить ежемесячную награду")
    async def monthly(self, inter: disnake.AppCmdInter):
        data = await get_user_data(inter.author.id)
        can_claim, wait = can_claim_reward(data, "monthly_ts", 2592000)

        if not can_claim:
            embed = disnake.Embed(
                description=f"⏳ Ты уже получал ежемесячную награду. Приходи снова <t:{format_timestamp(wait)}:R>.",
                color=disnake.Color.orange()
            )
            await inter.send(embed=embed, ephemeral=True)
            return

        reward = get_reward_amount("monthly")
        data["wallet"] += reward
        data["monthly_ts"] = datetime.now()
        await update_user_data(inter.author.id, data)

        embed = disnake.Embed(
            title="🗓 Ежемесячная награда",
            description=f"Ты получил **{reward} {CURRENCY}**. Возвращайся через месяц!",
            color=disnake.Color.purple()
        )
        await inter.send(embed=embed)


def setup(bot):
    bot.add_cog(RewardCommands(bot))