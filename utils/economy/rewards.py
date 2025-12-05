import random
from datetime import datetime, timedelta
from typing import Tuple

def can_claim_reward(data: dict, key: str, cooldown: int) -> Tuple[bool, int]:
    now = datetime.now()
    if key not in data:
        return True, 0
    last_time = data[key]
    if isinstance(last_time, str):
        last_time = datetime.fromisoformat(last_time)
    elapsed = (now - last_time).total_seconds()
    if elapsed >= cooldown:
        return True, 0
    return False, int(cooldown - elapsed)

def format_timestamp(seconds: int) -> int:
    return int((datetime.now() + timedelta(seconds=seconds)).timestamp())

def get_reward_amount(type_: str) -> int:
    if type_ == "daily":
        return random.randint(300, 600)
    if type_ == "weekly":
        return random.randint(2000, 4000)
    if type_ == "monthly":
        return random.randint(7000, 10000)
    return 0
