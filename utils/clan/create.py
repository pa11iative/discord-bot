from utils.database import clans
import disnake

async def create_clan_document(name: str, tag: str, author: disnake.Member, role: disnake.Role, created_at) -> None:
    await clans.insert_one({
        "name": name,
        "tag": tag.upper(),
        "owner_id": author.id,
        "deputies": [],
        "members": [author.id],
        "bank": 0,
        "created_at": created_at.isoformat(),
        "level": 1,
        "xp": 0,
        "role_id": role.id
    })
