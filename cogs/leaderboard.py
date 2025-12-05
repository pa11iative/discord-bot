import disnake
from disnake.ext import commands
from utils.database import users, clans
from config import CURRENCY, EMBED_COLOR


class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="leaderboard", description="Топ участников и кланов")
    async def leaderboard(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        await self.send_leaderboard(inter)

    async def send_leaderboard(self, inter: disnake.ApplicationCommandInteraction):
        class LeaderboardView(disnake.ui.View):
            def __init__(self, author: disnake.User):
                super().__init__(timeout=60)
                self.author = author
                self.page = 0
                self.category = "balance"
                self.pages = []

                self.add_item(CategorySelect(self))

            async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
                return interaction.author.id == self.author.id

            @disnake.ui.button(emoji="⬅️", style=disnake.ButtonStyle.gray, row=1)
            async def previous_button(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
                if not self.pages:
                    return
                self.page = (self.page - 1) % len(self.pages)
                embed = await self.create_embed()
                await interaction.response.edit_message(embed=embed, view=self)

            @disnake.ui.button(emoji="➡️", style=disnake.ButtonStyle.gray, row=1)
            async def next_button(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
                if not self.pages:
                    return
                self.page = (self.page + 1) % len(self.pages)
                embed = await self.create_embed()
                await interaction.response.edit_message(embed=embed, view=self)

            async def update_pages(self):
                data = []

                if self.category.startswith("clans"):
                    async for clan in clans.find():
                        data.append({
                            "name": clan.get("name", "Без имени"),
                            "tag": clan.get("tag", ""),
                            "xp": clan.get("xp", 0),
                            "bank": clan.get("bank", 0),
                            "level": clan.get("level", 0)
                        })

                    if self.category == "clans_level":
                        data.sort(key=lambda c: c["level"], reverse=True)
                    elif self.category == "clans_bank":
                        data.sort(key=lambda c: c["bank"], reverse=True)

                else:
                    async for user in users.find():
                        uid = user["_id"]
                        wallet = user.get("wallet", 0)
                        bank = user.get("bank", 0)
                        total = wallet + bank
                        messages = user.get("messages_sent", 0)
                        voice = user.get("voice_time", 0)
                        level = user.get("level", 0)
                        exp = user.get("exp", 0)

                        if self.category == "messages" and messages == 0:
                            continue
                        if self.category == "voice" and voice == 0:
                            continue
                        if self.category == "level" and level == 0:
                            continue

                        data.append({
                            "id": uid,
                            "wallet": wallet,
                            "bank": bank,
                            "total": total,
                            "messages_sent": messages,
                            "voice_time": voice,
                            "level": level,
                            "exp": exp
                        })

                    if self.category == "balance":
                        data.sort(key=lambda u: u["total"], reverse=True)
                    elif self.category == "voice":
                        data.sort(key=lambda u: u["voice_time"], reverse=True)
                    elif self.category == "messages":
                        data.sort(key=lambda u: u["messages_sent"], reverse=True)
                    elif self.category == "level":
                        data.sort(key=lambda u: (u["level"], u["exp"]), reverse=True)

                self.pages = [data[i:i + 10] for i in range(0, len(data), 10)]
                if self.page >= len(self.pages):
                    self.page = 0

            async def create_embed(self):
                if not self.pages:
                    return disnake.Embed(
                        title="📊 Топ",
                        description="Нет данных по выбранной категории.",
                        color=EMBED_COLOR
                    )

                page = self.pages[self.page]
                cat_name = {
                    "balance": "Баланс",
                    "voice": "Голосовая активность",
                    "messages": "Отправленные сообщения",
                    "level": "Уровень",
                    "clans_level": "Кланы по уровню",
                    "clans_bank": "Кланы по балансу"
                }.get(self.category, self.category)

                embed = disnake.Embed(
                    title=f"📊 Топ — {cat_name} (стр. {self.page + 1}/{len(self.pages)})",
                    color=EMBED_COLOR
                )

                desc = ""
                for i, entry in enumerate(page, start=1 + self.page * 10):
                    if self.category.startswith("clans"):
                        if self.category == "clans_level":
                            desc += f"**#{i} {entry['name']}** [`{entry['tag']}`] — ⭐ Уровень {entry['level']} (XP: {entry['xp']})\n\n"
                        elif self.category == "clans_bank":
                            desc += f"**#{i} {entry['name']}** [`{entry['tag']}`] — 🏦 Банк: {entry['bank']}{CURRENCY}\n\n"
                    else:
                        member = inter.guild.get_member(entry["id"])
                        tag = member.mention if member else f"Пользователь {entry['id']}"

                        if self.category == "balance":
                            desc += (
                                f"**#{i} {tag}**\n"
                                f"💰 Кошелёк: `{entry['wallet']}`{CURRENCY}, "
                                f"🏦 Банк: `{entry['bank']}`{CURRENCY}, "
                                f"📟 Всего: `{entry['total']}`{CURRENCY}\n\n"
                            )
                        elif self.category == "voice":
                            voice_minutes = entry.get("voice_time", 0)
                            hours = voice_minutes // 60
                            minutes = voice_minutes % 60
                            desc += f"**#{i} {tag}** — 🎧 **`{hours}`ч `{minutes}`м**\n\n"
                        elif self.category == "messages":
                            desc += f"**#{i} {tag}** — 💬 {entry['messages_sent']} сообщений\n\n"
                        elif self.category == "level":
                            desc += f"**#{i} {tag}** — ⭐ Уровень {entry['level']} (EXP: {entry['exp']})\n\n"

                embed.description = desc
                embed.set_footer(text="Выбери категорию с помощью меню ниже.")
                return embed

        class CategorySelect(disnake.ui.StringSelect):
            def __init__(self, parent_view: LeaderboardView):
                self.parent_view = parent_view
                options = [
                    disnake.SelectOption(label="Баланс", value="balance", emoji="💰"),
                    disnake.SelectOption(label="Голосовая активность", value="voice", emoji="🎧"),
                    disnake.SelectOption(label="Отправленные сообщения", value="messages", emoji="💬"),
                    disnake.SelectOption(label="Уровень", value="level", emoji="⭐"),
                    disnake.SelectOption(label="Кланы по уровню", value="clans_level", emoji="🏆"),
                    disnake.SelectOption(label="Кланы по балансу", value="clans_bank", emoji="🏦"),
                ]
                super().__init__(placeholder="Выберите категорию рейтинга", options=options, row=0)

            async def callback(self, interaction: disnake.MessageInteraction):
                self.parent_view.category = self.values[0]
                self.parent_view.page = 0
                await self.parent_view.update_pages()
                embed = await self.parent_view.create_embed()
                await interaction.response.edit_message(embed=embed, view=self.parent_view)

        view = LeaderboardView(inter.author)
        await view.update_pages()
        embed = await view.create_embed()
        await inter.edit_original_message(embed=embed, view=view)


def setup(bot):
    bot.add_cog(Leaderboard(bot))
