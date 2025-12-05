from utils.database import get_user_data, update_user_data
from config import CURRENCY, EMBED_COLOR
import disnake

async def deposit_money(user_id: int, amount: int) -> disnake.Embed:
    data = await get_user_data(user_id)

    if amount <= 0:
        return disnake.Embed(
            description="❌ Сумма должна быть положительной.",
            color=disnake.Color.red()
        )

    if data["wallet"] < amount:
        return disnake.Embed(
            description="💸 У тебя недостаточно денег в кошельке.",
            color=disnake.Color.red()
        )

    data["wallet"] -= amount
    data["bank"] += amount
    await update_user_data(user_id, data)

    return disnake.Embed(
        description=f"✅ Ты положил **{amount} {CURRENCY}** в банк.",
        color=EMBED_COLOR
    )

async def withdraw_money(user_id: int, amount: int) -> disnake.Embed:
    data = await get_user_data(user_id)

    if amount <= 0:
        return disnake.Embed(
            description="❌ Сумма должна быть положительной.",
            color=disnake.Color.red()
        )

    if data["bank"] < amount:
        return disnake.Embed(
            description="🏦 У тебя недостаточно денег в банке.",
            color=disnake.Color.red()
        )

    data["bank"] -= amount
    data["wallet"] += amount
    await update_user_data(user_id, data)

    return disnake.Embed(
        description=f"✅ Ты снял **{amount} {CURRENCY}** из банка.",
        color=EMBED_COLOR
    )

async def transfer_money(sender_user, receiver_user, amount: int) -> disnake.Embed:
    if sender_user.id == receiver_user.id:
        return disnake.Embed(
            description="❌ Нельзя перевести деньги самому себе.",
            color=disnake.Color.red()
        )

    if receiver_user.bot:
        return disnake.Embed(
            description="🤖 Нельзя переводить деньги ботам.",
            color=disnake.Color.red()
        )

    sender = await get_user_data(sender_user.id)
    receiver = await get_user_data(receiver_user.id)

    if amount <= 0:
        return disnake.Embed(
            description="❌ Сумма должна быть положительной.",
            color=disnake.Color.red()
        )

    if sender["wallet"] < amount:
        return disnake.Embed(
            description="💸 У тебя недостаточно денег в кошельке.",
            color=disnake.Color.red()
        )

    sender["wallet"] -= amount
    receiver["wallet"] += amount

    await update_user_data(sender_user.id, sender)
    await update_user_data(receiver_user.id, receiver)

    return disnake.Embed(
        description=f"📤 Ты перевёл **{amount} {CURRENCY}** пользователю {receiver_user.mention}.",
        color=EMBED_COLOR
    )
