import disnake
from disnake.ext import commands
from disnake import Embed
from utils.database import get_user_data, update_user_data
from utils.economy.crime import can_use_command, get_robbery_result
from config import CURRENCY, EMBED_COLOR
import random
from datetime import datetime


class CrimeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="crime", description="Попробовать совершить преступление (шанс провала)")
    async def crime(self, inter: disnake.AppCmdInter):
        data = await get_user_data(inter.author.id)
        can_use, wait = await can_use_command(data, "crime_ts", 86400)
        if not can_use:
            retry_at = int(datetime.now().timestamp() + wait)
            return await inter.send(
                embed=Embed(
                    description=f"⏳ Ты уже совершал преступление. Попробуй снова <t:{retry_at}:R>.",
                    color=disnake.Color.orange()
                ), ephemeral=True)

        success = random.random() < 0.5
        amount = random.randint(100, 300)
        if amount > data["wallet"]:
            success = True
        if success:
            data["wallet"] += amount
            desc = f"✅ Ты успешно совершил преступление и украл **{amount} {CURRENCY}**!"
            color = disnake.Color.green()
        else:
            data["wallet"] = max(0, data["wallet"] - amount)
            desc = f"🚨 Тебя поймали! Ты заплатил штраф **{amount} {CURRENCY}**."
            color = disnake.Color.red()

        data["crime_ts"] = datetime.now()
        await update_user_data(inter.author.id, data)

        await inter.send(embed=Embed(title="💣 Преступление", description=desc, color=color))

    @commands.slash_command(name="beg", description="Попрошайничать деньги у прохожих")
    async def beg(self, inter: disnake.AppCmdInter):
        data = await get_user_data(inter.author.id)
        can_use, wait = await can_use_command(data, "beg_ts", 86400)
        if not can_use:
            retry_at = int(datetime.now().timestamp() + wait)
            return await inter.send(
                embed=Embed(
                    description=f"⏳ Ты уже попрошайничал. Попробуй снова <t:{retry_at}:R>.",
                    color=disnake.Color.orange()
                ), ephemeral=True)

        amount = random.randint(50, 200)
        data["wallet"] += amount
        data["beg_ts"] = datetime.now()
        await update_user_data(inter.author.id, data)

        responses = [
            f"🥺 Добрый человек дал тебе **{amount} {CURRENCY}**.",
            f"😢 Кто-то пожалел тебя и дал **{amount} {CURRENCY}**.",
            f"🪙 Ты нашёл **{amount} {CURRENCY}** на улице!",
        ]

        await inter.send(embed=Embed(title="🙌 Попрошайничество", description=random.choice(responses), color=EMBED_COLOR))

    @commands.slash_command(name="rob", description="Ограбить другого участника")
    async def rob(self, inter: disnake.AppCmdInter, target: disnake.Member):
        if target.bot or target.id == inter.author.id:
            return await inter.send("❌ Ты не можешь ограбить этого пользователя.", ephemeral=True)

        robber_data = await get_user_data(inter.author.id)

        if robber_data.get("level", 0) < 10:
            return await inter.send(
                embed=disnake.Embed(
                    description="❌ Для ограбления нужен 10 уровень!",
                    color=disnake.Color.red()
                ),
                ephemeral=True
            )

        can_use, wait = await can_use_command(robber_data, "rob_ts", 86400)
        if not can_use:
            retry_at = int(datetime.now().timestamp() + wait)
            return await inter.send(
                embed=disnake.Embed(
                    description=f"⏳ Ты уже грабил. Попробуй снова <t:{retry_at}:R>.",
                    color=disnake.Color.orange()
                ),
                ephemeral=True
            )

        victim_data = await get_user_data(target.id)

        if victim_data["wallet"] < 200:
            return await inter.send(
                f"❌ У {target.mention} слишком мало денег, чтобы его грабить.",
                ephemeral=True
            )

        success, amount, message, color = get_robbery_result(victim_data["wallet"], target.mention)

        if success:
            robber_data["wallet"] += amount
            victim_data["wallet"] -= amount
        else:
            robber_data["wallet"] = max(0, robber_data["wallet"] - amount)

        robber_data["rob_ts"] = datetime.now()

        await update_user_data(inter.author.id, robber_data)
        await update_user_data(target.id, victim_data)

        await inter.send(
            embed=disnake.Embed(
                title="🔫 Ограбление",
                description=message,
                color=color
            )
        )

def setup(bot):
    bot.add_cog(CrimeCog(bot))