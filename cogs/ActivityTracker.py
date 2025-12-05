import disnake
from disnake.ext import commands, tasks
from utils.database import get_user_data, update_user_data, clans
from config import LEVEL_ROLES, AFK_CHANNEL_ID

class ActivityTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_activity = {}
        self.voice_check_loop.start()

    def cog_unload(self):
        self.voice_check_loop.cancel()

    def exp_for_level(self, level: int) -> int:
        return 100 + level * 20

    async def add_exp_and_money_to_clan(self, user_id: int, exp_gain: int, money_gain: int):
        clan = await clans.find_one({"members": user_id})
        if not clan:
            return

        current_xp = clan.get("xp", 0)
        current_level = clan.get("level", 0)
        current_bank = clan.get("bank", 0)
        weekexp = clan.get("weekly_exp", 0) + 1

        new_xp = current_xp + exp_gain
        new_bank = current_bank + money_gain

        leveled_up = False
        if current_xp + 1 >= 1000 + (current_level - 1) * 250:
            new_xp=0
            current_level += 1
            leveled_up = True

        await clans.update_one({"_id": clan["_id"]}, {
            "$set": {
                "xp": new_xp,
                "level": current_level,
                "bank": new_bank,
                "weekly_exp": weekexp
            }
        })

        if leveled_up:
            print(f"🏰 Клан {clan['name']} повысил уровень до {current_level}!")

    async def check_level_roles(self, member: disnake.Member, new_level: int):
        for level, role_id in LEVEL_ROLES.items():
            if new_level >= level:
                role = member.guild.get_role(role_id)
                if role and role not in member.roles:
                    try:
                        await member.add_roles(role, reason=f"Достиг уровень {level}")
                    except disnake.Forbidden:
                        print(f"❌ Не удалось выдать роль {role.name} участнику {member.display_name}")

    async def handle_level_up(self, member: disnake.Member, user: dict, exp_gain: int, money_gain: int):
        old_level = user.get("level", 0)
        total_exp = user.get("exp", 0) + exp_gain

        new_level = old_level
        if total_exp >= 100 + old_level * 20:
            new_level+=1
            total_exp = 0
        user["exp"] = total_exp
        user["weekly_exp"] +=1
        user["wallet"] = user.get("wallet", 0) + money_gain
        user["level"] = new_level

        if new_level > old_level:
            print(f"🆙 {member.display_name} повысил уровень: {old_level} → {new_level}")
            await self.check_level_roles(member, new_level)

        await update_user_data(member.id, user)
        await self.add_exp_and_money_to_clan(member.id, exp_gain, money_gain)

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.author.bot:
            return

        user = await get_user_data(message.author.id)
        user["messages_sent"] = user.get("messages_sent", 0) + 1
        user["weekly_messages"] = user.get("weekly_messages", 0) + 1
  
        exp_gain = 1
        money_gain = 1
        
        await self.handle_level_up(message.author, user, exp_gain, money_gain)

    @tasks.loop(seconds=60)
    async def voice_check_loop(self):
        try:
            for guild in self.bot.guilds:
                for voice_channel in guild.voice_channels:
                    for member in voice_channel.members:
                        if len(voice_channel.members) == 1:
                            continue
                        if (member.voice.self_deaf and member.voice.self_mute) or member.voice.afk or member.voice.self_deaf:
                            continue
                        if member.bot:
                            continue

                        user = await get_user_data(member.id)
                        user["voice_time"] = user.get("voice_time", 0) + 1
                        user["weekly_voice_time"] = user.get("weekly_voice_time", 0) + 1
                        
                        await self.handle_level_up(member, user, 1, 1)
        except Exception as e:
            print(f"Ошибка в voice_check_loop: {e}")

def setup(bot):
    bot.add_cog(ActivityTracker(bot))
