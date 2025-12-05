import disnake
from disnake.ext import commands
from config import CURRENCY, EMBED_COLOR
from utils.database import get_user_data, update_user_data
from utils.economy import games


class GameCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def update_game_stats(self, user_id: int):
        """Обновляет статистику игр"""
        data = await get_user_data(user_id)
        data["weekly_games"] = data.get("weekly_games", 0) + 1
        await update_user_data(user_id, data)

    @commands.slash_command(name="coinflip", description="Подбросить монетку (игра на деньги)")
    async def coinflip(
        self, 
        inter: disnake.AppCmdInter,
        ставка: int,
        выбор: str = commands.Param(choices=["орёл", "решка"])
    ):
        data = await get_user_data(inter.author.id)

        if ставка <= 0 or data["wallet"] < ставка:
            embed = disnake.Embed(
                description="❌ Недостаточно средств или некорректная ставка.",
                color=disnake.Color.red()
            )
            await inter.send(embed=embed, ephemeral=True)
            return

        win, результат = games.coinflip(выбор)
        data["wallet"] += ставка if win else -ставка
        await update_user_data(inter.author.id, data)
        await self.update_game_stats(inter.author.id)  # Добавляем +1 к играм

        embed = disnake.Embed(
            title="🪙 Монетка",
            description=(
                f"**Твой выбор:** {выбор}\n"
                f"**Результат:** {результат}\n\n"
                f"{'🎉 Ты выиграл' if win else '💸 Ты проиграл'} **{ставка} {CURRENCY}**!"
            ),
            color=EMBED_COLOR
        )
        await inter.send(embed=embed)

    @commands.slash_command(name="slots", description="Игровой автомат (слоты)")
    async def slots(self, inter: disnake.AppCmdInter, ставка: int):
        data = await get_user_data(inter.author.id)

        if ставка <= 0 or data["wallet"] < ставка:
            embed = disnake.Embed(
                description="❌ Недостаточно средств или некорректная ставка.",
                color=disnake.Color.red()
            )
            await inter.send(embed=embed, ephemeral=True)
            return

        symbols = games.roll_slots()
        line = " | ".join(symbols)
        win = symbols.count(symbols[0]) == 3
        won_amount = ставка * 2 if win else 0

        data["wallet"] += won_amount if win else -ставка
        await update_user_data(inter.author.id, data)
        await self.update_game_stats(inter.author.id)  # Добавляем +1 к играм

        embed = disnake.Embed(
            title="🎰 Слоты",
            description=(
                f"**Результат:** {line}\n\n"
                f"{'🎉 Джекпот! Ты выиграл' if win else '😢 Ты проиграл'} **{won_amount if win else ставка} {CURRENCY}**!"
            ),
            color=EMBED_COLOR
        )
        await inter.send(embed=embed)

    @commands.slash_command(name="rps", description="Камень, ножницы, бумага против бота")
    async def rps(
        self,
        inter: disnake.AppCmdInter,
        ставка: int,
        выбор: str = commands.Param(choices=["камень", "ножницы", "бумага"])
    ):
        data = await get_user_data(inter.author.id)

        if ставка <= 0 or data["wallet"] < ставка:
            embed = disnake.Embed(
                description="❌ Недостаточно средств или некорректная ставка.",
                color=disnake.Color.red()
            )
            await inter.send(embed=embed, ephemeral=True)
            return

        результат, бот_выбор = games.rps(выбор)

        if результат == "победа":
            data["wallet"] += ставка
        elif результат == "проигрыш":
            data["wallet"] -= ставка

        await update_user_data(inter.author.id, data)
        await self.update_game_stats(inter.author.id)  # Добавляем +1 к играм

        embed = disnake.Embed(
            title="✊ Бумага, камень, ножницы",
            description=(
                f"**Ты выбрал:** {выбор}\n"
                f"**Бот выбрал:** {бот_выбор}\n\n"
                f"**Результат:** {результат.title()}!\n"
                f"{'🎉 Ты получил' if результат == 'победа' else '💸 Ты потерял' if результат == 'проигрыш' else '⚖ Ничья, ты не потерял ничего'} **{ставка} {CURRENCY}**"
            ),
            color=EMBED_COLOR
        )
        await inter.send(embed=embed)

    @commands.slash_command(name="dice", description="Кубик (1-6) против бота")
    async def dice(self, inter: disnake.AppCmdInter, ставка: int):
        data = await get_user_data(inter.author.id)

        if ставка <= 0 or data["wallet"] < ставка:
            embed = disnake.Embed(
                description="❌ Недостаточно средств или некорректная ставка.",
                color=disnake.Color.red()
            )
            await inter.send(embed=embed, ephemeral=True)
            return

        user_roll, bot_roll = games.dice_roll()

        if user_roll > bot_roll:
            data["wallet"] += ставка
            result_text = f"🎉 Ты победил и получил **{ставка} {CURRENCY}**!"
        elif user_roll < bot_roll:
            data["wallet"] -= ставка
            result_text = f"💸 Ты проиграл **{ставка} {CURRENCY}**."
        else:
            result_text = f"⚖ Ничья! Никто не выиграл и не проиграл."

        await update_user_data(inter.author.id, data)
        await self.update_game_stats(inter.author.id)  # Добавляем +1 к играм

        embed = disnake.Embed(
            title="🎲 Бросок кубика",
            description=(
                f"**Ты выбросил:** 🎲 {user_roll}\n"
                f"**Бот выбросил:** 🎲 {bot_roll}\n\n"
                f"{result_text}"
            ),
            color=EMBED_COLOR
        )
        await inter.send(embed=embed)

def setup(bot):
    bot.add_cog(GameCommands(bot))