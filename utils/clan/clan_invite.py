import disnake
from disnake.ui import View, Button

class JoinClanView(View):
    def __init__(self, clan_id, user_id, guild_id, bot, timeout=3600):
        super().__init__(timeout=timeout)
        self.clan_id = clan_id
        self.user_id = user_id
        self.guild_id = guild_id
        self.bot = bot
        self.joined = False

    @disnake.ui.button(label="Присоединиться к клану", style=disnake.ButtonStyle.green)
    async def join_button(self, button: Button, inter: disnake.MessageInteraction):
        if inter.author.id != self.user_id:
            return await inter.response.send_message("⛔ Это приглашение не для тебя.", ephemeral=True)

        from utils.database import clans
        clan = await clans.find_one({"_id": self.clan_id})
        if not clan:
            return await inter.response.send_message("❌ Клан не найден.", ephemeral=True)

        if inter.author.id in clan["members"]:
            return await inter.response.send_message("Вы уже в этом клане.", ephemeral=True)

        await clans.update_one(
            {"_id": self.clan_id},
            {
                "$push": {"members": inter.author.id},
                "$unset": {f"invited.{str(inter.author.id)}": ""}
            }
        )

        guild = self.bot.get_guild(self.guild_id)
        if not guild:
            return await inter.response.send_message("❌ Не удалось найти сервер для выдачи роли.", ephemeral=True)

        member = guild.get_member(inter.author.id)
        if not member:
            return await inter.response.send_message("❌ Вы не участник этого сервера.", ephemeral=True)

        role_id = clan.get("role_id")
        if not role_id:
            return await inter.response.send_message("❌ В базе не указана роль клана.", ephemeral=True)

        role = guild.get_role(int(role_id))
        if not role:
            return await inter.response.send_message("❌ Роль клана не найдена на сервере (возможно, удалена вручную).", ephemeral=True)

        try:
            await member.add_roles(role, reason="Вступление в клан")
        except Exception as e:
            return await inter.response.send_message(f"❌ Не удалось выдать роль: {e}", ephemeral=True)

        self.joined = True
        for child in self.children:
            child.disabled = True
            child.label = "✅ Вы присоединились"
            child.style = disnake.ButtonStyle.green

        await inter.response.edit_message(
            content=f"✅ Вы успешно вступили в клан и получили роль **{role.name}**!",
            view=self
        )
        self.stop()

    async def on_timeout(self):
        if not self.joined:
            for item in self.children:
                item.disabled = True
                item.label = "⏱ Время вышло"
                item.style = disnake.ButtonStyle.gray
            try:
                await self.message.edit(view=self)
            except Exception:
                pass
