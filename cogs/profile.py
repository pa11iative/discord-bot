import disnake
from disnake.ext import commands

from utils.database import get_user_data
from utils.profile_image import generate_profile_card

class ProfileCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="profile", description="Показать профиль участника")
    async def profile(self, inter: disnake.AppCmdInter, member: disnake.Member = None):
        await inter.response.defer()

        member = member or inter.author
        data = await get_user_data(member.id)

        file = await generate_profile_card(member, data, bot=self.bot)
        await inter.edit_original_message(file=file)

def setup(bot):
    bot.add_cog(ProfileCog(bot))
