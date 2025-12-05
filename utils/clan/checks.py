from disnake import Member
from config import REQUIRED_ROLE_ID
from utils.database import clans

async def has_required_role(member: Member) -> bool:
    return REQUIRED_ROLE_ID in [role.id for role in member.roles]

async def is_already_in_clan(user_id: int) -> bool:
    return await clans.find_one({"members": user_id}) is not None

async def is_name_or_tag_taken(name: str, tag: str) -> bool:
    return await clans.find_one({"$or": [{"name": name}, {"tag": tag.upper()}]}) is not None
