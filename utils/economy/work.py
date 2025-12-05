import random
from datetime import datetime, timedelta
from typing import Tuple

async def can_work(data: dict) -> Tuple[bool, int]:
    now = datetime.now()
    if "work_ts" not in data:
        return True, 0
    elapsed = (now - data["work_ts"]).total_seconds()
    cooldown = 3600
    if elapsed >= cooldown:
        return True, 0
    return False, cooldown - elapsed


def get_work_reward() -> Tuple[int, str]:
    jobs = [
        "💻 Программист", "🧹 Дворник", "🚕 Таксист",
        "👨‍🍳 Повар", "💼 Менеджер", "🧑‍🎨 Художник", "📦 Курьер"
    ]
    reward = random.randint(100, 300)
    job = random.choice(jobs)
    return reward, job


def format_next_work_timestamp(data: dict) -> int:
    if "work_ts" not in data:
        return 0
    next_time = data["work_ts"] + timedelta(hours=1)
    return int(next_time.timestamp())
