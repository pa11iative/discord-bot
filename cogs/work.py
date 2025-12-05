import disnake
from disnake.ext import commands, tasks
from utils.database import get_user_data, update_user_data
from utils.economy.work import can_work, get_work_reward, format_next_work_timestamp
from config import EMBED_COLOR, CURRENCY
from datetime import datetime, timedelta


class WorkCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.work_reminders = {}

    @commands.slash_command(name="work", description="Поработать и заработать монеты")
    async def work(self, inter: disnake.AppCmdInter):
        data = await get_user_data(inter.author.id)
        can_work_flag, wait_time = await can_work(data)

        if not can_work_flag:
            retry_at = format_next_work_timestamp(data)
            embed = disnake.Embed(
                description=(
                    f"⏳ Ты уже работал недавно.\n"
                    f"Следующая работа доступна <t:{retry_at}:R>."
                ),
                color=disnake.Color.orange()
            )
            await inter.send(embed=embed, ephemeral=True)
            return

        reward, job = get_work_reward()

        data["wallet"] += reward
        data["work_ts"] = datetime.now()
        await update_user_data(inter.author.id, data)

        embed = disnake.Embed(
            title="🛠 Работа",
            description=(
                f"Ты поработал как **{job}** и заработал **{reward} {CURRENCY}**!\n"
                f"Следующая работа доступна <t:{format_next_work_timestamp(data)}:R>."
            ),
            color=EMBED_COLOR
        )

        class ReminderButton(disnake.ui.View):
            def __init__(self, bot, user_id, timeout=60):
                super().__init__(timeout=timeout)
                self.bot = bot
                self.user_id = user_id
                self.reminded = False
                self.message = None  # Чтобы сохранить сообщение для on_timeout

            @disnake.ui.button(label="🔔 Упомянуть позже", style=disnake.ButtonStyle.secondary)
            async def remind_later(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
                if self.reminded:
                    await interaction.response.send_message(
                        "Ты уже поставил напоминание.", ephemeral=True
                    )
                    return

                reminder_time = datetime.now() + timedelta(hours=1)
                self.reminded = True
                button.disabled = True
                await interaction.response.edit_message(view=self)

                self.bot.get_cog("WorkCommand").work_reminders[interaction.user.id] = {
                    "channel": interaction.channel,
                    "user": interaction.user,
                    "remind_at": reminder_time
                }

                await interaction.followup.send(
                    embed=disnake.Embed(
                        description=f"⏳ Я напомню тебе через час, {interaction.user.mention}.",
                        color=disnake.Color.green()
                    ), ephemeral=True
                )

            async def on_timeout(self):
                for child in self.children:
                    if isinstance(child, disnake.ui.Button):
                        child.disabled = True
                if self.message:
                    try:
                        await self.message.edit(view=self)
                    except Exception:
                        pass

        view = ReminderButton(self.bot, inter.author.id)
        response = await inter.send(embed=embed, view=view)
        view.message = await inter.original_message()

    @commands.Cog.listener()
    async def on_ready(self):
        self.check_reminders.start()

    @tasks.loop(seconds=30)
    async def check_reminders(self):
        now = datetime.now()
        to_remove = []

        for user_id, info in self.work_reminders.items():
            if now >= info["remind_at"]:
                try:
                    await info["channel"].send(
                        f"{info['user'].mention}, пришло время снова поработать! Используй команду `/work`. 🛠"
                    )
                except Exception:
                    pass
                to_remove.append(user_id)

        for uid in to_remove:
            self.work_reminders.pop(uid, None)

def setup(bot):
    bot.add_cog(WorkCommand(bot))
