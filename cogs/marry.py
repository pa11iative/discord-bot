import disnake
from disnake.ext import commands
from utils.database import get_user_data, update_user_data
from typing import Optional, Dict
import asyncio
from datetime import datetime, timedelta


class MarrySystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_proposals: Dict[int, dict] = {}  # {proposer_id: proposal_data}

    async def safe_send_dm(self, user: disnake.User, content=None, **kwargs):
        try:
            if user.dm_channel is None:
                await user.create_dm()
            return await user.dm_channel.send(content=content, **kwargs)
        except:
            return None

    async def safe_fetch_user(self, user_id: int) -> Optional[disnake.User]:
        try:
            return await self.bot.fetch_user(user_id)
        except (disnake.NotFound, disnake.HTTPException):
            return None

    @commands.slash_command(name="marry", description="Брачная система")
    async def marry(self, ctx):
        pass

    @marry.sub_command(name="propose", description="Сделать брачное предложение")
    async def propose(
        self,
        ctx: disnake.ApplicationCommandInteraction,
        target: disnake.Member
    ):
        try:
            if target.bot:
                return await ctx.send("❌ Нельзя сделать предложение боту!", ephemeral=True)
            if target.id == ctx.author.id:
                return await ctx.send("❌ Нельзя сделать предложение самому себе!", ephemeral=True)
            author_data, target_data = await asyncio.gather(
                get_user_data(ctx.author.id),
                get_user_data(target.id)
            )
            
            if author_data.get("marry") or target_data.get("marry"):
                return await ctx.send("❌ Один из вас уже состоит в браке!", ephemeral=True)
            embed = disnake.Embed(
                title="💍 Брачное предложение",
                description=f"{ctx.author.mention} предлагает вам вступить в брак!\n",
                color=0xFF69B4
            )
            embed.set_thumbnail(url=ctx.author.display_avatar.url)
            
            view = disnake.ui.View(timeout=3600)
            view.add_item(disnake.ui.Button(
                style=disnake.ButtonStyle.green,
                label="Принять",
                custom_id=f"marry_accept_{ctx.author.id}"
            ))
            view.add_item(disnake.ui.Button(
                style=disnake.ButtonStyle.red,
                label="Отклонить",
                custom_id=f"marry_reject_{ctx.author.id}"
            ))
            dm_msg = await self.safe_send_dm(target, embed=embed, view=view)
            if not dm_msg:
                return await ctx.send(
                    f"❌ Не удалось отправить предложение {target.mention}. Возможно, у него закрыты ЛС.",
                    ephemeral=True
                )
            self.active_proposals[ctx.author.id] = {
                "target_id": target.id,
                "dm_message_id": dm_msg.id
            }
            await ctx.send(
                f"✅ Брачное предложение отправлено {target.mention} в личные сообщения!",
                ephemeral=True
            )
            
        except Exception as e:
            await ctx.send(f"❌ Произошла ошибка: {str(e)}", ephemeral=True)

    @commands.Cog.listener()
    async def on_button_click(self, inter: disnake.MessageInteraction):
        try:
            if not inter.data.custom_id.startswith(("marry_accept_", "marry_reject_")):
                return
            proposer_id = int(inter.data.custom_id.split("_")[-1])
            proposal = self.active_proposals.get(proposer_id)
            
            if not proposal or proposal["target_id"] != inter.author.id:
                return await inter.send("❌ Это предложение не для вас или устарело!", ephemeral=True)
            
            if inter.data.custom_id.startswith("marry_accept_"):
                await asyncio.gather(
                    update_user_data(proposer_id, {"marry": inter.author.id}),
                    update_user_data(inter.author.id, {"marry": proposer_id})
                )
                proposer = await self.bot.fetch_user(proposer_id)
                await inter.response.edit_message(
                    embed=disnake.Embed(
                        title="💒 Брак заключен!",
                        description=f"Вы приняли предложение от {proposer.mention}!",
                        color=0x00FF00
                    ),
                    view=None
                )
                
                await self.safe_send_dm(
                    proposer,
                    embed=disnake.Embed(
                        title="💒 Брак заключен!",
                        description=f"{inter.author.mention} принял(а) ваше брачное предложение!",
                        color=0x00FF00
                    )
                )
                
            else:
                proposer = await self.bot.fetch_user(proposer_id)
                await inter.response.edit_message(
                    embed=disnake.Embed(
                        title="💔 Предложение отклонено",
                        description=f"Вы отклонили предложение от {proposer.mention}.",
                        color=0xFF0000
                    ),
                    view=None
                )
                
                await self.safe_send_dm(
                    proposer,
                    embed=disnake.Embed(
                        title="💔 Предложение отклонено",
                        description=f"{inter.author.mention} отклонил(а) ваше брачное предложение.",
                        color=0xFF0000
                    )
                )
            self.active_proposals.pop(proposer_id, None)
            
        except Exception as e:
            print(f"Error in button click: {e}")
            await inter.send("❌ Произошла ошибка при обработке вашего выбора", ephemeral=True)

    @marry.sub_command(name="divorce", description="Расторгнуть брак")
    async def divorce(
        self,
        ctx: disnake.ApplicationCommandInteraction,
        confirm: bool = commands.Param(
            default=False,
            description="Подтвердить развод (необратимо)"
        )
    ):
        try:
            user_data = await get_user_data(ctx.author.id)
            if not user_data or not user_data.get("marry"):
                return await ctx.send("❌ Вы не состоите в браке!", ephemeral=True)
            
            spouse_id = user_data["marry"]
            spouse = await self.bot.fetch_user(spouse_id)
            
            if not confirm:
                embed = disnake.Embed(
                    title="⚠️ Подтверждение развода",
                    description=f"Вы действительно хотите развестись с {spouse.mention if spouse else 'вашим супругом(ой)'}?",
                    color=disnake.Color.orange()
                )
                embed.add_field(
                    name="Это действие необратимо!",
                    value="Для подтверждения используйте команду с параметром `confirm=True`"
                )
                
                if not await self.safe_send_dm(ctx.author, embed=embed):
                    return await ctx.send(
                        "❌ Не удалось отправить подтверждение в ЛС. Проверьте настройки приватности.",
                        ephemeral=True
                    )
                
                return await ctx.send(
                    "✅ Запрос на подтверждение развода отправлен в ваши ЛС!",
                    ephemeral=True
                )
            
            # Подтвержденный развод
            await asyncio.gather(
                update_user_data(ctx.author.id, {"marry": None}),
                update_user_data(spouse_id, {"marry": None})
            )
            
            # Уведомление обеих сторон
            await ctx.send(
                embed=disnake.Embed(
                    title="💔 Брак расторгнут",
                    description=f"Вы развелись с {spouse.mention if spouse else 'вашим супругом(ой)'}.",
                    color=disnake.Color.red()
                ),
                ephemeral=True
            )
            
            await self.safe_send_dm(
                spouse,
                embed=disnake.Embed(
                    title="💔 Брак расторгнут",
                    description=f"{ctx.author.mention} развелся(ась) с вами.",
                    color=disnake.Color.red()
                )
            )
            
        except Exception as e:
            await ctx.send(f"❌ Произошла ошибка: {str(e)}", ephemeral=True)

    @marry.sub_command(name="info", description="Показать информацию о браке")
    async def marry_info(
        self,
        ctx: disnake.ApplicationCommandInteraction,
        member: Optional[disnake.Member] = None
    ):
        try:
            target = member or ctx.author
            if not target:
                return await ctx.send("❌ Пользователь не найден", ephemeral=True)

            # Получаем данные из базы
            user_data = await get_user_data(target.id)
            
            if not user_data or not user_data.get("marry"):
                embed = disnake.Embed(
                    title=f"Брачный статус {target.display_name}",
                    description="Не состоит в браке",
                    color=disnake.Color.light_grey()
                )
                embed.set_thumbnail(url=target.display_avatar.url)
                return await ctx.send(embed=embed)
            
            # Получаем информацию о супруге
            spouse_id = user_data["marry"]
            spouse = await self.safe_fetch_user(spouse_id)
            
            # Создаем embed
            embed = disnake.Embed(
                title=f"Брачный статус {target.display_name}",
                color=disnake.Color.blue()
            )
            
            # Основная информация
            embed.add_field(
                name="👤 Пользователь",
                value=f"{target.mention}",
                inline=True
            )
            embed.add_field(
                name="💍 Супруг(а)",
                value=f"{spouse.mention if spouse else '❌ Неизвестный пользователь'}",
                inline=True
            )
            
            if target.id != ctx.author.id:
                embed.set_footer(text=f"Запрошено {ctx.author.display_name}", 
                            icon_url=ctx.author.display_avatar.url)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Произошла ошибка: {str(e)}", ephemeral=True)


def setup(bot):
    bot.add_cog(MarrySystem(bot))