import random
from typing import Tuple

def coinflip(user_choice: str) -> Tuple[bool, str]:
    result = random.choice(["орёл", "решка"])
    return user_choice == result, result

def roll_slots() -> list:
    symbols = ["🍒", "🍋", "🔔", "💎", "7️⃣"]
    return [random.choice(symbols) for _ in range(3)]

def rps(user_choice: str) -> Tuple[str, str]:
    choices = ["камень", "ножницы", "бумага"]
    bot_choice = random.choice(choices)

    if user_choice == bot_choice:
        return "ничья", bot_choice
    wins = {
        "камень": "ножницы",
        "ножницы": "бумага",
        "бумага": "камень"
    }
    return ("победа" if wins[user_choice] == bot_choice else "проигрыш", bot_choice)

def dice_roll() -> Tuple[int, int]:
    return random.randint(1, 6), random.randint(1, 6)
