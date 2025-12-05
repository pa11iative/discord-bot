import disnake
from disnake.ext import commands, tasks
from datetime import datetime, timedelta
from pytz import timezone
import logging
import asyncio
import io
from PIL import Image, ImageDraw, ImageFont
import aiohttp

from utils.database import users, clans
from config import EMBED_COLOR, CURRENCY, REPORT_CHANNEL_ID

class WeeklyReport(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        self.last_report = None
        self.weekly_report.start()

    def cog_unload(self):
        self.weekly_report.cancel()

    async def draw_text_centered(self, draw, text, position, font, fill_color):
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = position[0] - text_width // 2
        y = position[1] - text_height // 2
        draw.text((x, y), text, font=font, fill=fill_color)

    @tasks.loop(minutes=1)
    async def weekly_report(self):
        try:
            now = datetime.now(timezone("Europe/Moscow"))
            if now.weekday() == 6 and now.hour == 18 and 0 <= now.minute < 1:
                if self.last_report is None or (now - self.last_report) > timedelta(hours=23):
                    await self.send_weekly_summary()
                    self.last_report = now
                    await asyncio.sleep(60)
        except Exception as e:
            self.logger.error(f"Error in weekly report task: {e}", exc_info=True)

    async def send_weekly_summary(self):
        try:
            self.logger.info("Starting weekly report generation...")
            
            channel = self.bot.get_channel(REPORT_CHANNEL_ID)
            if not channel:
                self.logger.error(f"Report channel {REPORT_CHANNEL_ID} not found")
                return
            if not channel.permissions_for(channel.guild.me).send_messages:
                self.logger.error(f"Bot has no permissions to send messages in {channel}")
                return
            top_data = await asyncio.gather(
                users.find({"weekly_messages": {"$gt": 0}}).sort("weekly_messages", -1).limit(1).to_list(1),
                users.find({"weekly_voice_time": {"$gt": 0}}).sort("weekly_voice_time", -1).limit(1).to_list(1),
                clans.find({"weekly_exp": {"$gt": 0}}).sort("weekly_exp", -1).limit(1).to_list(1)
            )
            top_chat, top_voice, top_clan = top_data

            lb = Image.open("assets/leaderboard.png").convert("RGBA")
            draw = ImageDraw.Draw(lb)
            semibold = ImageFont.truetype("assets/gilroy-semibold.ttf", 20)
            mask = Image.new("L", (55,55), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, 55,55), fill=255)
            if top_chat:
                member = await self.bot.get_or_fetch_user(top_chat[0]["_id"])
                if member:
                    nick = member.name
                    if len(nick) > 13:
                        nick = nick[:13] + '...'
                    print(draw, nick, (619,258), semibold, "white")
                    await self.draw_text_centered(draw, nick, (973,317), semibold, "white")
                    async with aiohttp.ClientSession() as session:
                        async with session.get(member.display_avatar.url) as resp:
                            avatar_bytes = await resp.read()
                    avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA").resize((55,55))
                    avatar.putalpha(mask)
                    lb.paste(avatar, (944,243), avatar)
            if top_voice:
                member = await self.bot.get_or_fetch_user(top_voice[0]["_id"])
                if member:
                    nick = member.name
                    if len(nick) > 16:
                        nick = nick[:16] + '...'
                    await self.draw_text_centered(draw, nick, (639,249), semibold, "white")
                    async with aiohttp.ClientSession() as session:
                        async with session.get(member.display_avatar.url) as resp:
                            avatar_bytes = await resp.read()
                    avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA").resize((55,55))
                    avatar.putalpha(mask)
                    lb.paste(avatar, (611,173), avatar)
            if top_clan:
                nick = top_clan[0]['name']
                if len(nick) > 16:
                    nick = nick[:16] + '...'
                plus = Image.open("assets/clan.png").convert("RGBA").resize((55,55))
                plus.putalpha(mask)
                lb.paste(plus, (292,115), plus)
                await self.draw_text_centered(draw, nick, (320,189), semibold, "white")

            buffer = io.BytesIO()
            lb.save(buffer, format="PNG")
            buffer.seek(0)
            file = disnake.File(buffer, filename="profile.png")
            await channel.send(file=file)
            await self.reset_weekly_stats()
        except Exception as e:
            self.logger.error(f"Error sending weekly summary: {e}", exc_info=True)


    async def reset_weekly_stats(self):
        try:
            result_users = await users.update_many({}, {
                "$set": {
                    "weekly_messages": 0,
                    "weekly_voice_time": 0,
                    "weekly_games": 0,
                    "weekly_exp": 0,
                }
            })
            result_clans = await clans.update_many({}, {
                "$set": {
                    "weekly_exp": 0,
                }
            })
            self.logger.info(f"Reset stats: users={result_users.modified_count}, clans={result_clans.modified_count}")
        except Exception as e:
            self.logger.error(f"Error resetting weekly stats: {e}")


def setup(bot):
    bot.add_cog(WeeklyReport(bot))