import disnake
from disnake.ext import commands
from disnake.ui import Select, View, Modal, TextInput

class RecruitmentCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.channel_id = 1406893512120602654

    @commands.command(name="набор")
    async def recruitment(self, ctx: commands.Context):
        embed = disnake.Embed(
            title="Набор в STAFF сервера",
            description=(
                "**Что нужно от тебя:**\n"
                f"<a:arrow_move:1405134362227507270>Возраст от 16 лет\n"
                f"<a:arrow_move:1405134362227507270>Свободное время\n"
                f"<a:arrow_move:1405134362227507270>Адекватность\n"
                f"<a:arrow_move:1405134362227507270>Умение работать в команде\n\n"
                "**Что мы предлагаем:**\n"
                f"<a:arrow_move:1405134362227507270>Дружный коллектив\n"
                f"<a:arrow_move:1405134362227507270>Поддержку руководства\n"
                f"<a:arrow_move:1405134362227507270>Полезный опыт\n"
                f"<a:arrow_move:1405134362227507270>Бонусы и привилегии (дискорд нитро, кастомные роли и т.п)"
            ),
            color=0x2F3136
        )
        
        # Добавляем картинку (замените URL на свою)
        embed.set_image(url="https://media.discordapp.net/attachments/1404005383089029192/1409798292728057987/nabor.png?ex=68aeb079&is=68ad5ef9&hm=ebd8f70b74e278156e8ac242fa6ff1f8c383c6e863dd7541e9f75f9cbfdd16b1&=&format=webp&quality=lossless&width=2404&height=1014")
        
        # Добавляем нижний текст с инструкцией
        embed.set_footer(text="Выберите роль из меню ниже, чтобы подать заявку")
        
        view = RoleSelectView(self.bot, self.channel_id)
        await ctx.send(embed=embed, view=view)

class RoleSelect(Select):
    def __init__(self, bot: commands.Bot, channel_id: int):
        self.bot = bot
        self.channel_id = channel_id
        super().__init__(
            placeholder="Выберите должность",
            options=[
                disnake.SelectOption(
                    label="Модератор",
                    description="Оставить заявку на модератора",
                    value="moderator"
                ),
                disnake.SelectOption(
                    label="Саппорт",
                    description="Оставить заявку на саппорта",
                    value="support"
                ),
                disnake.SelectOption(
                    label="Ивентер",
                    description="Оставить заявку на ивентера",
                    value="eventer"
                ),
                disnake.SelectOption(
                    label="Game Support",
                    description="Оставить заявку на game support",
                    value="game_support"
                ),
                disnake.SelectOption(
                    label="Креатив",
                    description="Оставить заявку на креатива",
                    value="creative"
                )
            ]
        )

    async def callback(self, interaction: disnake.MessageInteraction):
        role_name = self.values[0].replace('_', ' ').title()
        modal = ApplicationModal(role_name, self.bot, self.channel_id)
        await interaction.response.send_modal(modal)

class RoleSelectView(View):
    def __init__(self, bot: commands.Bot, channel_id: int):
        super().__init__(timeout=None)
        self.add_item(RoleSelect(bot, channel_id))

class ApplicationModal(Modal):
    def __init__(self, role_name: str, bot: commands.Bot, channel_id: int):
        self.role_name = role_name
        self.bot = bot
        self.channel_id = channel_id
        
        components = [
            TextInput(
                label="Личные данные",
                placeholder="Ваше имя, возраст и часовой пояс\nПример: Иван, 18 лет, MSK (UTC+3)",
                custom_id="personal_info",
                style=disnake.TextInputStyle.paragraph,
                max_length=150,
                required=True
            ),
            TextInput(
                label="Опыт работы и о себе",
                placeholder="Был ли опыт работы? Расскажите о себе",
                custom_id="experience_about",
                style=disnake.TextInputStyle.paragraph,
                max_length=600,
                required=True
            ),
            TextInput(
                label="Почему именно вы?",
                placeholder="Почему мы должны выбрать вас?",
                custom_id="why_you",
                style=disnake.TextInputStyle.paragraph,
                max_length=400,
                required=True
            ),
            TextInput(
                label="Доступное время",
                placeholder="Сколько времени готовы уделять? (например: 2-3 часа в день)",
                custom_id="time",
                style=disnake.TextInputStyle.short,
                max_length=50,
                required=True
            )
        ]
        
        super().__init__(
            title=f"Анкета на {role_name}",
            custom_id=f"app_modal_{role_name.lower()}",
            components=components
        )

    async def callback(self, interaction: disnake.ModalInteraction):
        channel = self.bot.get_channel(self.channel_id)
        
        if not channel:
            await interaction.response.send_message(
                "❌ Ошибка: канал для заявок не найден!",
                ephemeral=True
            )
            return

        embed = disnake.Embed(
            title=f"Новая заявка на {self.role_name}",
            color=0x2F3136,
            timestamp=interaction.created_at
        )
        
        embed.add_field(
            name="📌 Личные данные",
            value=interaction.text_values["personal_info"],
            inline=False
        )
        embed.add_field(
            name="📚 Опыт и информация",
            value=interaction.text_values["experience_about"],
            inline=False
        )
        embed.add_field(
            name="💡 Почему именно вы",
            value=interaction.text_values["why_you"],
            inline=False
        )
        embed.add_field(
            name="⏳ Доступное время",
            value=interaction.text_values["time"],
            inline=False
        )
        
        embed.set_author(
            name=interaction.author.name
        )
        embed.set_footer(text=f"ID пользователя: {interaction.author.id}")

        try:
            await channel.send(content=interaction.author.mention, embed=embed)
            await interaction.response.send_message(
                "✅ Ваша заявка успешно отправлена! Если вы подходите - с вами свяжется администрация.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Произошла ошибка при отправке заявки: {str(e)}",
                ephemeral=True
            )

def setup(bot: commands.Bot):
    bot.add_cog(RecruitmentCog(bot))