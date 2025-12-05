from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URL
from bson import ObjectId

client = AsyncIOMotorClient(MONGO_URL)
db = client["default_db"]
users = db["users"]
clans = db["clans"]
giveaways = db["giveaway"]
marriages = db["marriages"]
marriage_proposals = db["marriage_proposals"]
roles = db["roles"]
market = db["market"]

async def get_user_data(user_id: int) -> dict:
    user = await users.find_one({"_id": user_id})
    if user is None:
        default_data = {
            "_id": user_id,
            "wallet": 0,
            "bank": 0,
            "debt": 0,
            "messages_sent": 0,
            "weekly_messages": 0,
            "voice_time": 0,
            "weekly_voice_time": 0,
            "exp": 0,
            "weekly_exp": 0,
            "level": 0,
            "wallet": 0
        }
        await users.insert_one(default_data)
        return default_data
    return user

async def update_user_data(user_id: int, data: dict):
    set_fields = {k: v for k, v in data.items() if v is not None}
    unset_fields = {k: "" for k, v in data.items() if v is None}

    update_query = {}
    if set_fields:
        update_query["$set"] = set_fields
    if unset_fields:
        update_query["$unset"] = unset_fields

    if update_query:
        await users.update_one({"_id": user_id}, update_query, upsert=True)

async def get_clan_data(clan_id: int) -> dict:
    clan = await clans.find_one({"_id": clan_id})
    if clan is None:
        default_data = {
            "_id": clan_id,
            "name": "Без названия",
            "tag": "CLAN",
            "owner": None,
            "members": [],
            "level": 1,
            "exp": 0,
            "wallet": 0,
        }
        await clans.insert_one(default_data)
        return default_data
    return clan

async def update_clan_data(clan_id: int, data: dict):
    set_fields = {k: v for k, v in data.items() if v is not None}
    unset_fields = {k: "" for k, v in data.items() if v is None}

    update_query = {}
    if set_fields:
        update_query["$set"] = set_fields
    if unset_fields:
        update_query["$unset"] = unset_fields

    if update_query:
        await clans.update_one({"_id": clan_id}, update_query, upsert=True)

async def get_roles_data() -> dict:
    """Получить все данные о ролях"""
    roles_data = await roles.find_one({"_id": "roles_data"})
    if roles_data is None:
        default_data = {"_id": "roles_data"}
        await roles.insert_one(default_data)
        return default_data
    return roles_data

async def update_roles_data(data: dict):
    """Обновить данные о ролях"""
    set_fields = {k: v for k, v in data.items() if v is not None and k != "_id"}
    unset_fields = {k: "" for k, v in data.items() if v is None and k != "_id"}

    update_query = {}
    if set_fields:
        update_query["$set"] = set_fields
    if unset_fields:
        update_query["$unset"] = unset_fields

    if update_query:
        await roles.update_one({"_id": "roles_data"}, update_query, upsert=True)

async def get_market_data() -> dict:
    """Получить все данные о рынке"""
    market_data = await market.find_one({"_id": "market_data"})
    if market_data is None:
        default_data = {"_id": "market_data"}
        await market.insert_one(default_data)
        return default_data
    return market_data

async def update_market_data(data: dict):
    """Обновить данные о рынке"""
    set_fields = {k: v for k, v in data.items() if v is not None and k != "_id"}
    unset_fields = {k: "" for k, v in data.items() if v is None and k != "_id"}

    update_query = {}
    if set_fields:
        update_query["$set"] = set_fields
    if unset_fields:
        update_query["$unset"] = unset_fields

    if update_query:
        await market.update_one({"_id": "market_data"}, update_query, upsert=True)

async def get_role_by_id(role_db_id: str) -> dict:
    """Получить данные о конкретной роли по ID в базе"""
    roles_data = await get_roles_data()
    return roles_data.get(role_db_id, {})

async def remove_from_market(item_id: str):
    """Удалить товар с рынка"""
    market_data = await get_market_data()
    if item_id in market_data:
        del market_data[item_id]
        await update_market_data(market_data)

async def get_user_roles(user_id: int) -> list:
    """Получить все роли пользователя"""
    roles_data = await get_roles_data()
    user_roles = []
    
    for role_id, role_info in roles_data.items():
        if role_id == "_id":
            continue
        if role_info.get("owner_id") == user_id:
            user_roles.append((role_id, role_info))
    
    return user_roles

async def transfer_role_ownership(role_db_id: str, new_owner_id: int):
    """Передать владение ролью другому пользователю"""
    roles_data = await get_roles_data()
    if role_db_id in roles_data:
        roles_data[role_db_id]["owner_id"] = new_owner_id
        await update_roles_data(roles_data)
        return True
    return False