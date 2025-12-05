import disnake
from disnake.ext import commands, tasks
from utils.database import users
import aiohttp
import io
from PIL import Image, ImageDraw, ImageFont

class banner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @tasks.loop(seconds=10)
    async def change_banner(self):
        idd = users.find({"2hmessages": {"$gt": 0}}).sort("2hmessages", -1).limit(1)
        if idd:
            user = self.bot.get_or_fetch_user(idd)
            ban = Image.open("assets/banner.png").convert("RGBA")
            draw = ImageDraw.Draw(ban)
            semibold45 = ImageFont.truetype("assets/gilroy-semibold.ttf", 45)
            mask = Image.new("L", (93,93), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, 93,93), fill=255)
            async with aiohttp.ClientSession() as session:
                async with session.get(user.display_avatar.url) as resp:
                    avatar_bytes = await resp.read()
            avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA").resize((93,93))
            avatar.putalpha(mask)
            ban.paste(avatar, (112,372), avatar)
            nick = user.name
            if len(nick) > 16:
                nick = nick[:16] + '...'
            draw.text((234,429), nick, font=semibold45, fill="white")
            buffer = io.BytesIO()
            ban.save(buffer, format="PNG")
            buffer.seek(0)
            file = disnake.File(buffer, filename="profile.png")
            channel = self.bot.get_channel(1403694276331704425)
            await channel.send(file=file)
            
def setup(bot):
    bot.add_cog(banner(bot))

    
