from datetime import datetime

def calculate_interest(amount: int, rate: float) -> tuple[int, int]:
    interest = int(amount * rate)
    total = amount + interest
    return total, interest