import disnake

async def create_clan_role(guild: disnake.Guild, name: str, tag: str) -> disnake.Role:
    role_name = f"{name} [{tag.upper()}]"
    return await guild.create_role(
        name=role_name,
        mentionable=True,
        reason=f"Роль для клана {name} создана автоматически"
    )

async def assign_role(member: disnake.Member, role: disnake.Role):
    await member.add_roles(role, reason="Роль клана при создании клана")
