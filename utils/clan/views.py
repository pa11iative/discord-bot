import disnake
from disnake.ui import View, Select, Button, Modal, TextInput
from disnake import SelectOption, Embed, TextInputStyle
import dateutil.parser
from utils.database import clans


class RenameClanModal(Modal):
    def __init__(self, bot, clan_data, guild_id):
        self.bot = bot
        self.clan_data = clan_data
        self.guild_id = guild_id

        components = [
            TextInput(
                label="Новое имя клана",
                custom_id="new_name",
                max_length=32,
                style=TextInputStyle.short,
                placeholder="Например, Армия"
            ),
            TextInput(
                label="Новый тег клана",
                custom_id="new_tag",
                max_length=5,
                style=TextInputStyle.short,
                placeholder="Например, ARMY"
            )
        ]
        super().__init__(title="Изменение имени и тега клана", components=components)

    async def callback(self, interaction: disnake.ModalInteraction):
        new_name = interaction.text_values["new_name"]
        new_tag = interaction.text_values["new_tag"]

        await clans.update_one({"_id": self.clan_data["_id"]}, {"$set": {"name": new_name, "tag": new_tag}})

        role_id = self.clan_data.get("role_id")
        if role_id:
            guild = self.bot.get_guild(self.guild_id)
            role = guild.get_role(role_id)
            if role:
                try:
                    await role.edit(name=f"{new_name} [{new_tag}]")
                except Exception as e:
                    return await interaction.response.send_message(f"✅ Имя и тег клана обновлены в БД.\n⚠ Но не удалось изменить имя роли: {e}", ephemeral=True)

        await interaction.response.send_message(
            f"✅ Имя клана изменено на **{new_name}**\n"
            f"🏷 Новый тег: `{new_tag}`\n"
            f"📛 Имя роли обновлено.",
            ephemeral=True
        )



class ChangeColorModal(Modal):
    def __init__(self, bot, clan_data, guild_id):
        self.bot = bot
        self.clan_data = clan_data
        self.guild_id = guild_id
        components = [
            TextInput(
                label="HEX-цвет (например, #ff0000)",
                custom_id="color_hex",
                max_length=7,
                style=TextInputStyle.short
            )
        ]
        super().__init__(title="Новый цвет роли", components=components)

    async def callback(self, interaction: disnake.ModalInteraction):
        hex_code = interaction.text_values["color_hex"]
        try:
            color_int = int(hex_code.lstrip("#"), 16)
        except ValueError:
            return await interaction.response.send_message("❌ Неверный HEX код.", ephemeral=True)

        role_id = self.clan_data.get("role_id")
        if not role_id:
            return await interaction.response.send_message("❌ У клана нет привязанной роли.", ephemeral=True)

        guild = self.bot.get_guild(self.guild_id)
        role = guild.get_role(role_id)
        if role:
            try:
                await role.edit(color=disnake.Color(color_int))
            except Exception as e:
                return await interaction.response.send_message(f"❌ Не удалось изменить цвет роли: {e}", ephemeral=True)

        await clans.update_one({"_id": self.clan_data["_id"]}, {"$set": {"role_color": hex_code}})
        await interaction.response.send_message(f"✅ Цвет роли изменён на `{hex_code}`", ephemeral=True)


class ClanInfoView(View):
    def __init__(self, bot, clan_data, server_stats):
        super().__init__(timeout=300)
        self.bot = bot
        self.clan = clan_data
        self.server_stats = server_stats

        self.per_page = 10
        self.page = 0

        self.owner_id = clan_data["owner_id"]
        self.deputies_ids = clan_data.get("deputies", [])
        self.members_ids = [m for m in clan_data.get("members", []) if m not in self.deputies_ids and m != self.owner_id]

        self.select = Select(
            placeholder="Выберите категорию",
            options=[
                SelectOption(label="Информация", value="info", description="Детальная информация о клане"),
                SelectOption(label="Участники", value="members", description="Просмотр участников клана"),
                SelectOption(label="Управление кланом", value="manage", description="Изменить имя и цвет роли"),
            ],
            row=0
        )
        self.select.callback = self.select_callback
        self.add_item(self.select)

        self.prev_button = Button(label="⬅ Назад", style=disnake.ButtonStyle.gray)
        self.next_button = Button(label="Вперед ➔", style=disnake.ButtonStyle.gray)
        self.prev_button.callback = self.prev_page
        self.next_button.callback = self.next_page

    def exp_for_level(self, level: int) -> int:
        return 100 * level

    def get_level_by_exp(self, exp: int) -> int:
        level = 0
        while exp >= self.exp_for_level(level + 1):
            level += 1
        return level

    async def select_callback(self, inter: disnake.MessageInteraction):
        choice = self.select.values[0]

        if choice == "info":
            embed = await self._build_detailed_info_embed()
            await inter.response.send_message(embed=embed, ephemeral=True)

        elif choice == "members":
            embed = await self._build_members_embed()
            view = View()
            view.add_item(self.prev_button)
            view.add_item(self.next_button)
            self.update_buttons()
            await inter.response.send_message(embed=embed, view=view, ephemeral=True)

        elif choice == "manage":
            if inter.author.id != self.owner_id:
                return await inter.response.send_message("❌ Только основатель клана может управлять им.", ephemeral=True)

            embed = Embed(
                title=f"⚙ Управление кланом {self.clan['name']}",
                description="Выберите действие:",
                color=0x2F3136
            )
            view = View()
            view.add_item(Button(label="✏ Изменить имя клана", style=disnake.ButtonStyle.primary, custom_id="rename_clan"))
            view.add_item(Button(label="🎨 Изменить цвет роли", style=disnake.ButtonStyle.primary, custom_id="change_color"))

            async def rename_callback(button_inter):
                await button_inter.response.send_modal(RenameClanModal(self.bot, self.clan, button_inter.guild.id))


            async def color_callback(button_inter):
                await button_inter.response.send_modal(ChangeColorModal(self.bot, self.clan, inter.guild.id))

            view.children[0].callback = rename_callback
            view.children[1].callback = color_callback

            await inter.response.send_message(embed=embed, view=view, ephemeral=True)

    async def _build_detailed_info_embed(self) -> Embed:
        clan = self.clan
        owner_user = self.bot.get_user(self.owner_id) or await self.bot.fetch_user(self.owner_id)
        deputies_mentions = ", ".join(f"<@{uid}>" for uid in self.deputies_ids) if self.deputies_ids else "—"

        xp = clan.get("xp", 0)
        level = clan.get("level", 0)
        next_level_exp = 1000 + (level - 1) * 250
        current_level_exp = xp
        total_level_exp = next_level_exp
        current_level_exp = max(current_level_exp, 0)
        progress_percent = (current_level_exp / total_level_exp) * 100 if total_level_exp > 0 else 100
        filled_length = int(20 * current_level_exp / total_level_exp) if total_level_exp > 0 else 20
        progress_bar = "█" * filled_length + "░" * (20 - filled_length)

        total_voice_sec = self.server_stats.get("total_voice_time", 0)
        hours = total_voice_sec // 60
        minutes = total_voice_sec % 60
        total_messages = self.server_stats.get("total_messages", 0)

        created_at_str = clan.get('created_at')
        if created_at_str:
            dt = dateutil.parser.isoparse(created_at_str)
            unix_ts = int(dt.timestamp())
            created_at_formatted = f"<t:{unix_ts}:R>"
        else:
            created_at_formatted = "—"

        embed = Embed(
            title=f"📊 Детальная информация о клане {clan['name']} [`{clan['tag']}`]",
            color=0x2F3136
        )
        embed.add_field(name="Основатель", value=owner_user.mention if owner_user else f"<@{self.owner_id}>", inline=True)
        embed.add_field(name="Заместители", value=deputies_mentions, inline=True)
        embed.add_field(name="Банк клана", value=f"{clan.get('bank', 0)} {clan.get('currency', '')}", inline=True)
        embed.add_field(name="Уровень", value=f"{level} (XP: {current_level_exp} / {total_level_exp})", inline=True)
        embed.add_field(name="Создан", value=created_at_formatted, inline=True)
        embed.add_field(name="Прогресс до следующего уровня", value=f"{progress_bar} {progress_percent:.1f}%", inline=False)
        embed.add_field(name="Общее время в голосе", value=f"{hours} ч. {minutes} мин.", inline=True)
        embed.add_field(name="Отправлено сообщений", value=f"{total_messages}", inline=True)
        return embed

    async def _build_members_embed(self) -> Embed:
        lines = []
        owner_user = self.bot.get_user(self.owner_id) or await self.bot.fetch_user(self.owner_id)
        lines.append(f"**1. Основатель:** {owner_user.mention if owner_user else f'<@{self.owner_id}>'}")

        if self.deputies_ids:
            for idx, uid in enumerate(self.deputies_ids, start=2):
                user = self.bot.get_user(uid) or await self.bot.fetch_user(uid)
                lines.append(f"**{idx}. Заместитель:** {user.mention if user else f'<@{uid}>'}")

        start_index = 1 + len(self.deputies_ids) + 1
        start = self.page * self.per_page
        end = start + self.per_page
        paged_members = self.members_ids[start:end]

        for i, uid in enumerate(paged_members, start=start_index + start):
            user = self.bot.get_user(uid) or await self.bot.fetch_user(uid)
            lines.append(f"**{i}. Участник:** {user.mention if user else f'<@{uid}>'}")

        embed = Embed(
            title=f"👥 Участники клана ({len(self.clan.get('members', []))}) — страница {self.page + 1}",
            description="\n".join(lines) if lines else "Участников нет.",
            color=0x2F3136
        )
        return embed

    def update_buttons(self):
        total_pages = max((len(self.members_ids) - 1) // self.per_page, 0)
        self.prev_button.disabled = self.page == 0
        self.next_button.disabled = self.page >= total_pages

    async def prev_page(self, inter: disnake.MessageInteraction):
        if self.page > 0:
            self.page -= 1
            self.update_buttons()
            embed = await self._build_members_embed()
            view = View()
            view.add_item(self.prev_button)
            view.add_item(self.next_button)
            await inter.response.edit_message(embed=embed, view=view)
        else:
            await inter.response.defer()

    async def next_page(self, inter: disnake.MessageInteraction):
        total_pages = max((len(self.members_ids) - 1) // self.per_page, 0)
        if self.page < total_pages:
            self.page += 1
            self.update_buttons()
            embed = await self._build_members_embed()
            view = View()
            view.add_item(self.prev_button)
            view.add_item(self.next_button)
            await inter.response.edit_message(embed=embed, view=view)
        else:
            await inter.response.defer()
