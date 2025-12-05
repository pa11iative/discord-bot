import disnake
from disnake.ext import commands, tasks
from disnake import Option, OptionType
from datetime import datetime, timedelta
import asyncio
import random

from utils.database import giveaways, users
from config import EMBED_COLOR


class GiveawayCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_giveaways.start()

    def cog_unload(self):
        self.check_giveaways.cancel()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.emoji.name != "🎉":
            return
        giveaway_data = await giveaways.find_one({"message_id": payload.message_id})
        if not giveaway_data:
            return
        user = self.bot.get_user(payload.user_id)
        if user.bot:
            return
        user_data = await users.find_one({"_id": payload.user_id})
        if not user_data or user_data.get("level", 0) < 5:
            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            await message.remove_reaction(payload.emoji, user)

            embed = disnake.Embed(
                title="❌ Недостаточный уровень",
                description="Для участия в розыгрыше требуется 5 уровень или выше! Проверить уровень можно командой `/profile`",
                color=0xff0000
            )
            
            try:
                await user.send(embed=embed)
            except disnake.Forbidden:
                try:
                    ch = self.bot.get_channel(1140243006860038166)
                    await ch.send(f"{user.mention}", embed=embed, delete_after=30)
                except:
                    pass

    @commands.slash_command(name="giveaway", description="Запустить розыгрыш")
    async def giveaway(
        self,
        inter: disnake.ApplicationCommandInteraction,
        duration: str = commands.Param(name="длительность", description="Пример: 1h, 30m"),
        description: str = commands.Param(name="описание", description="Описание розыгрыша"),
        prize: str = commands.Param(name="награда", description="Приз за победу"),
    ):
        if not inter.author.guild_permissions.administrator:
            return await inter.response.send_message("❌ У тебя нет прав администратора для запуска розыгрыша.", ephemeral=True)
        
        await inter.response.defer(ephemeral=True)

        delta = self.parse_duration(duration)
        if delta is None:
            await inter.edit_original_message("❌ Неверный формат длительности. Пример: `1h`, `30m`, `2d`")
            return

        end_time = datetime.now() + delta

        embed = disnake.Embed(
            title="🎉 Розыгрыш!",
            description=f"**{description}**\n\n💎 **Награда:** {prize}\n🕒 Завершение: <t:{int(end_time.timestamp())}:R>",
            color=EMBED_COLOR
        )
        embed.set_image(url="https://media.discordapp.net/attachments/1407299495196098693/1409973145787568128/image.jpg?ex=68af5351&is=68ae01d1&hm=27426252fc9824bad53dd81593e559732e5c42a9f8f3a747f73439ab590caa10&=&format=webp&width=1802&height=1014")
        embed.set_footer(text=f"Нажмите на реакцию, чтобы участвовать в розыгрыше.", icon_url=inter.author.display_avatar.url)

        message = await inter.channel.send(embed=embed)
        await message.add_reaction("🎉")

        await giveaways.insert_one({
            "guild_id": inter.guild_id,
            "channel_id": inter.channel.id,
            "message_id": message.id,
            "description": description,
            "prize": prize,
            "end_time": end_time.timestamp()
        })

        await inter.followup.send("✅ Розыгрыш запущен!", ephemeral=True)

    @commands.slash_command(name="reroll", description="Перевыбрать победителя розыгрыша")
    async def reroll(
        self,
        inter: disnake.ApplicationCommandInteraction,
        message_id: str = commands.Param(name="айди_сообщения", description="ID сообщения розыгрыша")
    ):
        if not inter.author.guild_permissions.administrator:
            return await inter.response.send_message("❌ У тебя нет прав администратора для этой команды.", ephemeral=True)
        
        await inter.response.defer(ephemeral=True)

        try:
            message_id = int(message_id)
            channel = inter.channel
            message = await channel.fetch_message(message_id)
            
            participants = []
            for reaction in message.reactions:
                if str(reaction.emoji) == "🎉":
                    users_list = await reaction.users().flatten()
                    participants = [u for u in users_list if not u.bot]
                    break
            
            if not participants:
                return await inter.followup.send("❌ Нет участников для перевыбора.", ephemeral=True)
            
            winner = random.choice(participants)
            await channel.send(
                f"🎉 Победитель перевыбран! Новый победитель розыгрыша: {winner.mention}\n"
            )
            
            await inter.followup.send(f"✅ Новый победитель: {winner.mention}", ephemeral=True)
            
        except Exception as e:
            await inter.followup.send(f"❌ Ошибка: {str(e)}", ephemeral=True)

    def parse_duration(self, s: str) -> timedelta | None:
        try:
            num = int(s[:-1])
            unit = s[-1].lower()
            match unit:
                case 's': return timedelta(seconds=num)
                case 'm': return timedelta(minutes=num)
                case 'h': return timedelta(hours=num)
                case 'd': return timedelta(days=num)
        except:
            return None

    @tasks.loop(seconds=30)
    async def check_giveaways(self):
        now = datetime.now().timestamp()
        active = await giveaways.find({"end_time": {"$lte": now}}).to_list(length=None)

        for giveaway_data in active:
            try:
                channel = self.bot.get_channel(giveaway_data["channel_id"])
                if not channel:
                    await giveaways.delete_one({"_id": giveaway_data["_id"]})
                    continue

                message = await channel.fetch_message(giveaway_data["message_id"])

  
                participants = []
                for reaction in message.reactions:
                    if str(reaction.emoji) == "🎉":
                        async for user in reaction.users():
                            if user.bot:
                                continue
                            user_data = await users.find_one({"_id": user.id})
                            if user_data and user_data.get("level", 0) >= 5:
                                participants.append(user)
                        break

                embed = message.embeds[0]
                new_embed = embed.copy()

                if participants:
                    winner = random.choice(participants)
                    new_embed.add_field(name="🏆 Победитель", value=winner.mention)
                    await channel.send(
                        f"🎉 Розыгрыш завершен! Победитель: {winner.mention}\n"
                        f"💎 **Приз:** {giveaway_data['prize']}\n"
                    )
                else:
                    new_embed.add_field(name="❌ Победитель", value="Нет участников")
                    await channel.send(
                        f"🎉 Розыгрыш завершен! Нет участников.\n"
                        f"💎 **Приз:** {giveaway_data['prize']}\n"
                    )

                await message.edit(embed=new_embed)
                await giveaways.delete_one({"_id": giveaway_data["_id"]})

            except Exception as e:
                print(f"[GIVEAWAY ERROR] {e}")
                continue

def setup(bot):
    bot.add_cog(GiveawayCog(bot))