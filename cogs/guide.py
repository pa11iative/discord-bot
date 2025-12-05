import disnake
from disnake.ext import commands
from disnake import SelectOption, TextInputStyle
import json
import os
from config import EMBED_COLOR, TICKET_CATEGORY_ID, TICKET_ROLES
from asyncio import sleep

def load_guide_data():
    path = "data/guide.json"
    if not os.path.exists(path):
        return {}

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

class CloseTicketView(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @disnake.ui.button(label="Закрыть тикет", style=disnake.ButtonStyle.red, emoji="🔒")
    async def close_ticket(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.send_message("🔒 Тикет будет закрыт через 3 секунды...", ephemeral=True)
        await sleep(3)
        await inter.channel.delete()

class TicketModal(disnake.ui.Modal):
    def __init__(self, type_: str):
        title = "Жалоба на игрока" if type_ == "report" else "Вопрос по серверу"
        self.type_ = type_
        components = [
            disnake.ui.TextInput(
                label="Опишите суть",
                placeholder="Укажите все детали...",
                custom_id="description",
                style=TextInputStyle.paragraph,
                max_length=1000
            )
        ]
        super().__init__(title=title, components=components)

    async def callback(self, interaction: disnake.ModalInteraction):
        description = interaction.text_values["description"]
        guild = interaction.guild
        category = guild.get_channel(TICKET_CATEGORY_ID)

        for channel in category.text_channels:
            if channel.name == f"ticket-{interaction.author.name.lower()}":
                await interaction.response.send_message("❌ У вас уже есть открытый тикет. Пожалуйста, дождитесь ответа.", ephemeral=True)
                return

        overwrites = {
            guild.default_role: disnake.PermissionOverwrite(view_channel=False),
            interaction.author: disnake.PermissionOverwrite(view_channel=True, send_messages=True),
        }

        mentions = [interaction.author.mention]

        for role_id in TICKET_ROLES:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = disnake.PermissionOverwrite(view_channel=True, send_messages=True)
                mentions.append(role.mention)

        channel = await guild.create_text_channel(
            name=f"ticket-{interaction.author.name}",
            category=category,
            overwrites=overwrites
        )

        embed = disnake.Embed(
            title="Новый тикет",
            description=f"**Тип:** {self.type_}\n**Пользователь:** {interaction.author.mention}\n\n```{description}```",
            color=EMBED_COLOR
        )

        await channel.send(content=" ".join(mentions), embed=embed, view=CloseTicketView())
        await interaction.response.send_message("✅ Тикет создан!", ephemeral=True)

class TicketButtons(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

    @disnake.ui.button(label="Жалоба на игрока", style=disnake.ButtonStyle.danger)
    async def report_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.send_modal(TicketModal("Жалоба на игрока"))

    @disnake.ui.button(label="Вопрос по серверу", style=disnake.ButtonStyle.primary)
    async def question_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.send_modal(TicketModal("Вопрос по серверу"))

class GuideSelect(disnake.ui.StringSelect):
    def __init__(self):
        options = [
            SelectOption(label="Путеводитель", value="guide"),
            SelectOption(label="Правила", value="rules"),
            SelectOption(label="Список ролей", value="roles"),
            SelectOption(label="Тикеты", value="tickets"),
            SelectOption(label="Кланы", value="clans"),
        ]
        super().__init__(placeholder="Выберите раздел...", options=options, custom_id="guide_select")

    async def callback(self, interaction: disnake.MessageInteraction):
        selected = self.values[0]
        data = load_guide_data()

        if selected == "tickets":
            embed = disnake.Embed(
                title="🎟 Открытие тикета",
                description="Выберите тип обращения ниже:",
                color=EMBED_COLOR
            )
            await interaction.response.send_message(embed=embed, view=TicketButtons(), ephemeral=True)
            return

        sections = data.get(selected, [])
        if not sections:
            await interaction.response.send_message(f"❌ Раздел `{selected}` пуст или не найден.", ephemeral=True)
            return
        chunks = [sections[i:i + 10] for i in range(0, len(sections), 10)]
        first_chunk = chunks[0]
        embeds = []
        for entry in first_chunk:
            embed = disnake.Embed(
                title=entry.get("title", "Информация"),
                description=entry.get("description", ""),
                color=EMBED_COLOR
            )
            if image_url := entry.get("image_url"):
                embed.set_image(url=image_url)
            embeds.append(embed)
        await interaction.response.send_message(embeds=embeds, ephemeral=True)

        for chunk in chunks[1:]:
            embeds = []
            for entry in chunk:
                embed = disnake.Embed(
                    title=entry.get("title", "Информация"),
                    description=entry.get("description", ""),
                    color=EMBED_COLOR
                )
                if image_url := entry.get("image_url"):
                    embed.set_image(url=image_url)
                embeds.append(embed)
            await interaction.followup.send(embeds=embeds, ephemeral=True)

class GuideView(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(GuideSelect())

class Guide(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(GuideView())

    @commands.command(name="путеводитель")
    @commands.has_permissions(administrator=True)
    async def путеводитель(self, ctx):
        embed = disnake.Embed(color=EMBED_COLOR)
        embed.set_image(url="https://media.discordapp.net/attachments/1404005383089029192/1409798293055209552/putivoditel.png?ex=68aeb079&is=68ad5ef9&hm=fc00259582e87598822d1f6fd665012e987e8718655d57477db24887a7726c37&=&format=webp&quality=lossless&width=2404&height=1014")
        await ctx.send(embed=embed, view=GuideView()) 

    @commands.command(name="платныероли")
    @commands.has_permissions(administrator=True)
    async def гид(self, ctx):
        embed1 = disnake.Embed(color=EMBED_COLOR)
        embed1.set_image(url="https://media.discordapp.net/attachments/1404005383089029192/1404130522543951955/fame.png?ex=689a11f4&is=6898c074&hm=f863afa5af507f8d5e7e1d8646f9cf937d61b67c37b961137614e343c06a0154&=&format=webp&quality=lossless&width=2576&height=1046")
        embed2 = disnake.Embed(color=EMBED_COLOR)
        embed2.set_image(url="https://media.discordapp.net/attachments/1404005383089029192/1404130522992476190/senior_moderator.png?ex=689a11f4&is=6898c074&hm=17bf03d6521f26539e78dd66a02f1a39f5c6aa65c930e5637570427b14670f2e&=&format=webp&quality=lossless&width=2576&height=1046")
        await ctx.send(embeds=[embed1, embed2])

def setup(bot):
    bot.add_cog(Guide(bot))