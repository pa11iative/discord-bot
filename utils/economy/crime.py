from datetime import datetime, timedelta
import random
import disnake

async def can_use_command(data: dict, key: str, cooldown: int) -> tuple[bool, int]:
    now = datetime.now()
    last = data.get(key)
    if isinstance(last, str):
        last = datetime.fromisoformat(last)
    if not last:
        return True, 0
    elapsed = (now - last).total_seconds()
    return (elapsed >= cooldown), max(0, cooldown - elapsed)

def get_robbery_result(victim_wallet: int, target_mention: str) -> tuple[bool, int, str, disnake.Color]:
    success = random.random() < 0.6
    if success:
        percent = random.uniform(0.2, 0.3)
        amount = int(victim_wallet * percent)
        message = (
            f"💸 Ты успешно ограбил {target_mention} и получил **{amount}** монет "
            f"({int(percent * 100)}% от его кошелька)!"
        )
        color = disnake.Color.green()
        return True, amount, message, color
    else:
        fine = random.randint(100, 300)
        message = (
            f"🚔 Ты неудачно попытался ограбить {target_mention} и заплатил штраф **{fine}** монет."
        )
        color = disnake.Color.red()
        return False, fine, message, color
