import disnake
from disnake.ext import commands
from disnake import Embed
from config import CURRENCY, EMBED_COLOR, REQUIRED_ROLE_ID

from utils.clan.checks import has_required_role, is_already_in_clan, is_name_or_tag_taken
from utils.clan.helpers import create_clan_role, assign_role
from utils.clan.create import create_clan_document
from utils.database import clans, get_user_data, update_user_data
from utils.clan.clan_invite import JoinClanView
from utils.clan.views import ClanInfoView

CLAN_CREATION_COST = 100000

class Clan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="clan", description="Управление вашим кланом")
    async def clan(self, inter: disnake.AppCmdInter):
        pass

    @clan.sub_command(name="create", description="Создать свой клан")
    async def clan_create(
        self,
        inter: disnake.AppCmdInter,
        name: str = commands.Param(name="название", description="Название вашего клана"),
        tag: str = commands.Param(name="тег", description="Краткое обозначение (до 5 символов)")
    ):
        await inter.response.defer()

        if not await has_required_role(inter.author):
            return await inter.edit_original_message(embed=disnake.Embed(
                title="⛔ Нет доступа",
                description="У вас нет нужной роли для создания клана.\n Чтобы создать клан, пишите - <@&1140352720465821806> или <@&1140352899755561065>.",
                color=disnake.Color.red()
            ))

        if await is_already_in_clan(inter.author.id):
            return await inter.edit_original_message(embed=disnake.Embed(
                title="⛔ Уже в клане",
                description="Вы уже состоите в клане и не можете создать второй.",
                color=disnake.Color.red()
            ))

        if len(tag) > 5:
            return await inter.edit_original_message(embed=disnake.Embed(
                title="Ошибка",
                description="Тег не должен превышать **5 символов**.",
                color=disnake.Color.red()
            ))

        if await is_name_or_tag_taken(name, tag):
            return await inter.edit_original_message(embed=disnake.Embed(
                title="Ошибка",
                description="Клан с таким **названием** или **тегом** уже существует.",
                color=disnake.Color.red()
            ))

        try:
            role = await create_clan_role(inter.guild, name, tag)
        except Exception as e:
            return await inter.edit_original_message(embed=disnake.Embed(
                title="Ошибка создания роли",
                description=f"Не удалось создать роль для клана: {e}",
                color=disnake.Color.red()
            ))

        try:
            await assign_role(inter.author, role)
        except Exception as e:
            return await inter.edit_original_message(embed=disnake.Embed(
                title="Ошибка выдачи роли",
                description=f"Роль создана, но не удалось выдать её создателю: {e}",
                color=disnake.Color.red()
            ))

        await create_clan_document(name, tag, inter.author, role, inter.created_at)

        await inter.edit_original_message(embed=disnake.Embed(
            title="✅ Клан создан!",
            description=f"Вы успешно создали клан **{name}** [`{tag.upper()}`] и вам выдана роль {role.mention}",
            color=EMBED_COLOR
        ))

    @clan.sub_command(name="info", description="Информация о вашем или чужом клане")
    async def clan_info(self, inter: disnake.AppCmdInter, участник: disnake.Member = None):
        await inter.response.defer()

        target = участник or inter.author
        clan = await clans.find_one({"members": target.id})

        if not clan:
            return await inter.edit_original_message(embed=disnake.Embed(
                title="Клан не найден",
                description=f"У {target.mention} нет клана.",
                color=disnake.Color.red()
            ))

        all_member_ids = list(set(
            clan.get("members", []) + clan.get("deputies", []) + [clan["owner_id"]]
        ))

        total_voice_time = total_messages = total_exp = total_wallet = 0

        for uid in all_member_ids:
            data = await get_user_data(uid)
            total_voice_time += data.get("voice_time", 0)
            total_messages += data.get("messages_sent", 0)
            total_exp += data.get("exp", 0)
            total_wallet += data.get("wallet", 0)

        server_stats = {
            "total_voice_time": total_voice_time,
            "total_messages": total_messages,
            "total_exp": total_exp,
            "total_wallet": total_wallet,
        }

        view = ClanInfoView(self.bot, clan, server_stats)
        embed = await view._build_detailed_info_embed()
        await inter.edit_original_message(embed=embed, view=view)

    @clan.sub_command(name="delete", description="Удалить свой клан (только для создателя)")
    async def clan_delete(self, inter: disnake.AppCmdInter):
        await inter.response.defer()

        clan = await clans.find_one({"owner_id": inter.author.id})

        if not clan:
            return await inter.edit_original_message(
                embed=disnake.Embed(
                    title="❌ Удаление невозможно",
                    description="Вы не являетесь создателем клана или не состоите в нём.",
                    color=disnake.Color.red()
                )
            )

        role_id = clan.get("role_id")
        if role_id:
            role = inter.guild.get_role(int(role_id))
            if role:
                try:
                    await role.delete(reason="Клан был удалён создателем")
                except Exception as e:
                    await inter.channel.send(f"⚠ Не удалось удалить роль: {e}")

        await clans.delete_one({"_id": clan["_id"]})

        await inter.edit_original_message(
            embed=disnake.Embed(
                title="🗑️ Клан удалён",
                description=f"Клан **{clan['name']}** [`{clan['tag']}`] был успешно удалён.",
                color=disnake.Color.orange()
            )
        )

    @clan.sub_command(name="leave", description="Покинуть текущий клан")
    async def clan_leave(self, inter: disnake.AppCmdInter):
        await inter.response.defer()

        clan = await clans.find_one({"members": inter.author.id})

        if not clan:
            return await inter.edit_original_message(
                embed=disnake.Embed(
                    title="❌ Вы не в клане",
                    description="Вы не состоите ни в одном клане.",
                    color=disnake.Color.red()
                )
            )

        if clan["owner_id"] == inter.author.id:
            return await inter.edit_original_message(
                embed=disnake.Embed(
                    title="⛔ Нельзя выйти",
                    description="Вы являетесь **создателем** клана. Используйте `/clan delete`.",
                    color=disnake.Color.red()
                )
            )

        await clans.update_one(
            {"_id": clan["_id"]},
            {
                "$pull": {
                    "members": inter.author.id,
                    "deputies": inter.author.id
                }
            }
        )

        role_id = clan.get("role_id")
        if role_id:
            role = inter.guild.get_role(int(role_id))
            if role and role in inter.author.roles:
                try:
                    await inter.author.remove_roles(role, reason="Пользователь покинул клан")
                except Exception as e:
                    await inter.channel.send(f"⚠ Не удалось снять роль: {e}")

        await inter.edit_original_message(
            embed=disnake.Embed(
                title="🚪 Вы покинули клан",
                description=f"Вы успешно вышли из клана **{clan['name']}**.",
                color=disnake.Color.orange()
            )
        )

    @clan.sub_command(name="invite", description="Пригласить участника в клан")
    async def clan_invite(
        self,
        inter: disnake.AppCmdInter,
        участник: disnake.Member = commands.Param(name="участник", description="Кого пригласить в клан")
    ):
        await inter.response.defer()

        clan = await clans.find_one({"members": inter.author.id})
        if not clan:
            return await inter.edit_original_message(
                embed=Embed(
                    title="❌ Ошибка",
                    description="Вы не состоите в клане.",
                    color=disnake.Color.red()
                )
            )

        if inter.author.id != clan.get("owner_id") and inter.author.id not in clan.get("deputies", []):
            return await inter.edit_original_message(
                embed=Embed(
                    title="⛔ Нет доступа",
                    description="Приглашать участников могут только основатель или заместители клана.",
                    color=disnake.Color.red()
                )
            )

        if участник.id in clan["members"]:
            return await inter.edit_original_message(
                embed=Embed(
                    title="ℹ️ Уже в клане",
                    description=f"{участник.mention} уже в вашем клане.",
                    color=disnake.Color.blurple()
                )
            )

        if await clans.find_one({"members": участник.id}):
            return await inter.edit_original_message(
                embed=Embed(
                    title="❌ Ошибка",
                    description="Этот пользователь уже в другом клане.",
                    color=disnake.Color.red()
                )
            )

        await clans.update_one(
            {"_id": clan["_id"]},
            {"$set": {f"invited.{str(участник.id)}": inter.created_at.isoformat()}}
        )

        embed = Embed(
            title="📨 Приглашение в клан",
            description=(
                f"Вас пригласили в клан **{clan['name']}** [`{clan['tag']}`]\n\n"
                f"Нажмите кнопку ниже, чтобы вступить!"
            ),
            color=disnake.Color.green()
        )

        view = JoinClanView(clan["_id"], участник.id, inter.guild.id, self.bot)

        try:
            await участник.send(embed=embed, view=view)
        except disnake.Forbidden:
            return await inter.edit_original_message(
                embed=Embed(
                    title="❌ Не удалось отправить приглашение",
                    description="Пользователь закрыл ЛС или запретил сообщения от бота.",
                    color=disnake.Color.red()
                )
            )

        await inter.edit_original_message(
            embed=Embed(
                title="✅ Приглашение отправлено",
                description=f"{участник.mention} получил приглашение в ЛС (действует 1 час).",
                color=disnake.Color.green()
            )
        )

    @clan.sub_command(name="kick", description="Выгнать участника из клана")
    async def clan_kick(
        self,
        inter: disnake.AppCmdInter,
        участник: disnake.Member = commands.Param(name="участник", description="Кого выгнать из клана")
    ):
        await inter.response.defer()

        clan = await clans.find_one({"members": inter.author.id})
        if not clan:
            return await inter.edit_original_message(
                embed=disnake.Embed(
                    title="❌ Ошибка",
                    description="Вы не состоите в клане.",
                    color=disnake.Color.red()
                )
            )

        is_owner = inter.author.id == clan["owner_id"]
        is_deputy = inter.author.id in clan.get("deputies", [])

        if not (is_owner or is_deputy):
            return await inter.edit_original_message(
                embed=disnake.Embed(
                    title="⛔ Нет прав",
                    description="Только лидер и заместители могут выгонять из клана.",
                    color=disnake.Color.red()
                )
            )

        if участник.id == clan["owner_id"]:
            return await inter.edit_original_message(
                embed=disnake.Embed(
                    title="⛔ Ошибка",
                    description="Нельзя выгнать создателя клана.",
                    color=disnake.Color.red()
                )
            )

        if участник.id not in clan["members"]:
            return await inter.edit_original_message(
                embed=disnake.Embed(
                    title="❌ Не в клане",
                    description=f"{участник.mention} не состоит в вашем клане.",
                    color=disnake.Color.red()
                )
            )

        await clans.update_one(
            {"_id": clan["_id"]},
            {
                "$pull": {
                    "members": участник.id,
                    "deputies": участник.id
                }
            }
        )

        role_id = clan.get("role_id")
        if role_id:
            role = inter.guild.get_role(int(role_id))
            if role and role in участник.roles:
                try:
                    await участник.remove_roles(role, reason="Исключение из клана")
                except Exception as e:
                    await inter.channel.send(f"⚠ Не удалось снять роль с {участник.mention}: {e}")

        await inter.edit_original_message(
            embed=disnake.Embed(
                title="👢 Участник исключён",
                description=f"{участник.mention} был исключён из клана и потерял роль.",
                color=disnake.Color.orange()
            )
        )

    @clan.sub_command(name="promote", description="Назначить заместителя клана")
    async def clan_promote(
        self,
        inter: disnake.AppCmdInter,
        участник: disnake.Member = commands.Param(name="участник", description="Кого назначить заместителем")
    ):
        await inter.response.defer()

        clan = await clans.find_one({"owner_id": inter.author.id})
        if not clan:
            return await inter.edit_original_message(
                embed=disnake.Embed(
                    title="⛔ Нет прав",
                    description="Только создатель клана может назначать заместителей.",
                    color=disnake.Color.red()
                )
            )

        if участник.id not in clan["members"]:
            return await inter.edit_original_message(
                embed=disnake.Embed(
                    title="❌ Ошибка",
                    description=f"{участник.mention} не состоит в вашем клане.",
                    color=disnake.Color.red()
                )
            )

        deputies = clan.get("deputies", [])
        if участник.id in deputies:
            return await inter.edit_original_message(
                embed=disnake.Embed(
                    title="ℹ️ Уже заместитель",
                    description=f"{участник.mention} уже является заместителем.",
                    color=disnake.Color.blurple()
                )
            )

        deputies.append(участник.id)
        await clans.update_one({"_id": clan["_id"]}, {"$set": {"deputies": deputies}})

        await inter.edit_original_message(
            embed=disnake.Embed(
                title="✅ Назначение",
                description=f"{участник.mention} теперь заместитель клана.",
                color=disnake.Color.green()
            )
        )

    @clan.sub_command(name="demote", description="Снять заместителя клана")
    async def clan_demote(
        self,
        inter: disnake.AppCmdInter,
        участник: disnake.Member = commands.Param(name="участник", description="Кого снять с должности заместителя")
    ):
        await inter.response.defer()

        clan = await clans.find_one({"owner_id": inter.author.id})
        if not clan:
            return await inter.edit_original_message(
                embed=disnake.Embed(
                    title="⛔ Нет прав",
                    description="Только создатель клана может снимать заместителей.",
                    color=disnake.Color.red()
                )
            )

        deputies = clan.get("deputies", [])
        if участник.id not in deputies:
            return await inter.edit_original_message(
                embed=disnake.Embed(
                    title="❌ Ошибка",
                    description=f"{участник.mention} не является заместителем.",
                    color=disnake.Color.red()
                )
            )

        deputies.remove(участник.id)
        await clans.update_one({"_id": clan["_id"]}, {"$set": {"deputies": deputies}})

        await inter.edit_original_message(
            embed=disnake.Embed(
                title="✅ Снятие",
                description=f"{участник.mention} больше не заместитель клана.",
                color=disnake.Color.green()
            )
        )

    @clan.sub_command(name="deposit", description="Внести деньги в банк клана")
    async def clan_deposit(
        self,
        inter: disnake.AppCmdInter,
        amount: int = commands.Param(name="сумма", description="Сумма для внесения", gt=0)
    ):
        await inter.response.defer()

        clan = await clans.find_one({"members": inter.author.id})
        if not clan:
            return await inter.edit_original_message(
                embed=Embed(
                    title="⛔ Ошибка",
                    description="Вы не состоите в клане.",
                    color=disnake.Color.red()
                )
            )

        user = await get_user_data(inter.author.id)
        wallet = user.get("wallet", 0)

        if amount > wallet:
            return await inter.edit_original_message(
                embed=Embed(
                    title="⛔ Ошибка",
                    description=f"У вас недостаточно средств в кошельке. Ваш баланс: {wallet}",
                    color=disnake.Color.red()
                )
            )

        user["wallet"] = wallet - amount
        await update_user_data(inter.author.id, user)

        new_bank = clan.get("bank", 0) + amount
        await clans.update_one({"_id": clan["_id"]}, {"$set": {"bank": new_bank}})

        embed = Embed(
            title="✅ Успешный депозит",
            description=f"Вы внесли в банк клана **{amount} {CURRENCY}**.\n"
                        f"Новый баланс банка: **{new_bank} {CURRENCY}**",
            color=disnake.Color.green()
        )
        await inter.edit_original_message(embed=embed)


    @clan.sub_command(name="withdraw", description="Снять деньги из банка клана")
    async def clan_withdraw(
        self,
        inter: disnake.AppCmdInter,
        amount: int = commands.Param(name="сумма", description="Сумма для снятия", gt=0)
    ):
        await inter.response.defer()

        clan = await clans.find_one({"members": inter.author.id})
        if not clan:
            return await inter.edit_original_message(
                embed=Embed(
                    title="⛔ Ошибка",
                    description="Вы не состоите в клане.",
                    color=disnake.Color.red()
                )
            )

        if inter.author.id != clan["owner_id"] and inter.author.id not in clan.get("deputies", []):
            return await inter.edit_original_message(
                embed=Embed(
                    title="⛔ Доступ запрещён",
                    description="Только основатель или заместители клана могут снимать деньги из банка.",
                    color=disnake.Color.red()
                )
            )

        bank = clan.get("bank", 0)
        if amount > bank:
            return await inter.edit_original_message(
                embed=Embed(
                    title="⛔ Ошибка",
                    description=f"В банке клана недостаточно средств. Баланс банка: {bank}",
                    color=disnake.Color.red()
                )
            )

        new_bank = bank - amount
        await clans.update_one({"_id": clan["_id"]}, {"$set": {"bank": new_bank}})

        user = await get_user_data(inter.author.id)
        user["wallet"] = user.get("wallet", 0) + amount
        await update_user_data(inter.author.id, user)

        embed = Embed(
            title="✅ Успешное снятие",
            description=f"Вы сняли из банка клана **{amount} {CURRENCY}**.\n"
                        f"Новый баланс банка: **{new_bank} {CURRENCY}**",
            color=disnake.Color.green()
        )
        await inter.edit_original_message(embed=embed)

def setup(bot):
    bot.add_cog(Clan(bot))
