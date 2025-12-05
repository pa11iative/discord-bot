from config import CURRENCY, EMBED_COLOR
from datetime import datetime
import disnake

def get_balance_embed(inter, user, data):
    wallet = data.get("wallet", 0)
    bank = data.get("bank", 0)
    level = data.get("level", 1)
    total = wallet + bank

    now = datetime.now()
    rewards = []

    if "daily_ts" not in data or (now - data["daily_ts"]).total_seconds() >= 86400:
        rewards.append("- `/daily`")
    if "weekly_ts" not in data or (now - data["weekly_ts"]).total_seconds() >= 604800:
        rewards.append("- `/weekly`")
    if "monthly_ts" not in data or (now - data["monthly_ts"]).total_seconds() >= 2592000:
        rewards.append("- `/monthly`")
    if "work_ts" not in data or (now - data["work_ts"]).total_seconds() >= 3600:
        rewards.append("- `/work`")

    embed = disnake.Embed(
        title=f"📊 Баланс — {user.display_name}",
        color=EMBED_COLOR
    )
    embed.description = (
        f"👛 **Наличные:** `{wallet}` {CURRENCY}\n"
        f"🏦 **В банке:** `{bank}` {CURRENCY}\n"
        f"💰 **Общий баланс:** `{total}` {CURRENCY}\n"
        f"🎖 **Уровень:** `{level}`\n\n"
        f"🎁 **Доступные награды:**\n" + "\n".join(rewards)
    )
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.set_footer(text=f"Запрошено: {inter.author}", icon_url=inter.author.display_avatar.url)
    return embed
