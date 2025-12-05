import disnake
from disnake.ext import commands
import re
from utils.database import get_user_data, update_user_data, get_roles_data, update_roles_data, get_market_data, update_market_data

class RoleShop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color_map = {
            "красный": disnake.Color.red(),
            "синий": disnake.Color.blue(),
            "зеленый": disnake.Color.green(),
            "зелёный": disnake.Color.green(),
            "желтый": disnake.Color.yellow(),
            "жёлтый": disnake.Color.yellow(),
            "оранжевый": disnake.Color.orange(),
            "фиолетовый": disnake.Color.purple(),
            "розовый": disnake.Color(0x7700ff),
            "белый": disnake.Color(0xffffff),
            "черный": disnake.Color(0x000000),
            "чёрный": disnake.Color(0x000000),
            "серый": disnake.Color.greyple()
        }

    @commands.slash_command(name="create_role", description="Создать новую роль (стоимость: 5000 монет)")
    async def create_role(self, inter: disnake.ApplicationCommandInteraction, 
                         название: str, 
                         цвет: str):
        """
        Parameters
        ----------
        название: Название роли
        цвет: Цвет роли (базовые цвета или HEX код)
        """
        # Проверка баланса
        data = await get_user_data(inter.author.id)
        if data["wallet"] < 5000:
            await inter.send("У тебя недостаточно монет (нужно 5000)!", ephemeral=True)
            return
        
        # Проверка и преобразование цвета
        color_obj = await self.parse_color(цвет)
        if not color_obj:
            await inter.send("Неверный цвет! Используй базовые цвета (красный, синий, зеленый, желтый, оранжевый, фиолетовый, розовый, белый, черный, серый) или HEX код (например, #FF0000)", ephemeral=True)
            return
        
        # Создание роли
        try:
            role = await inter.guild.create_role(
                name=название,
                color=color_obj,
                reason=f"Создана пользователем {inter.author}"
            )
            try:
                await inter.author.add_roles(role, reason="Создатель роли")
            except disnake.Forbidden:
                await inter.edit_original_response("У бота нет прав для выдачи ролей!")
                await role.delete(reason="Ошибка выдачи роли создателю")
                return
            except Exception as e:
                await inter.edit_original_response(f"Ошибка при выдаче роли: {e}")
                await role.delete(reason="Ошибка выдачи роли создателю")
                return
            # Обновление баланса
            data["wallet"] -= 5000
            await update_user_data(inter.author.id, data)
            
            # Сохранение информации о роли в БД
            roles_data = await get_roles_data()
            role_id = len(roles_data) + 1
            
            roles_data[str(role_id)] = {
                "role_id": role.id,
                "name": название,
                "owner_id": inter.author.id,
                "guild_id": inter.guild.id,
                "created_at": disnake.utils.utcnow().isoformat()
            }
            
            await update_roles_data(roles_data)
            
            await inter.send(f"Роль {role.mention} успешно создана! (ID: {role_id})", ephemeral=True)
            
        except Exception as e:
            await inter.send(f"Ошибка при создании роли: {e}", ephemeral=True)

    @commands.slash_command(name="sell", description="Выставить роль на продажу")
    async def sell_role(self, inter: disnake.ApplicationCommandInteraction, 
                    цена: int):
        """
        Parameters
        ----------
        цена: Цена в монетах
        """
        await inter.response.defer(ephemeral=True)
        
        # Получение ролей пользователя
        roles_data = await get_roles_data()
        user_roles = []
        
        for role_db_id, role_info in roles_data.items():
            if role_db_id == "_id":
                continue
            if role_info.get("owner_id") == inter.author.id:
                user_roles.append((role_db_id, role_info))
        
        if not user_roles:
            await inter.edit_original_response("У тебя нет ролей для продажи!")
            return
        
        # Создание выпадающего списка
        options = []
        for role_db_id, role_info in user_roles:
            guild = self.bot.get_guild(role_info["guild_id"])
            if guild:
                role = guild.get_role(role_info["role_id"])
                if role:
                    options.append(disnake.SelectOption(
                        label=role_info["name"][:25],  # Ограничение длины
                        value=role_db_id,
                        description=f"ID: {role_db_id}"[:50],
                        emoji="🎭"
                    ))
        
        if not options:
            await inter.edit_original_response("Не удалось найти твои роли на сервере!")
            return
        
        # Создание селект-меню
        select_menu = disnake.ui.Select(
            placeholder="Выбери роль для продажи",
            options=options[:25],
            custom_id=f"sell_role_select_{inter.author.id}"
        )
        
        view = disnake.ui.View()
        view.add_item(select_menu)
        view.timeout = 60
        
        # Отправка сообщения с выбором
        await inter.edit_original_response(
            "Выбери роль для продажи:",
            view=view
        )
        
        # Ожидание выбора
        try:
            select_inter: disnake.MessageInteraction = await self.bot.wait_for(
                "message_interaction",
                check=lambda i: i.data.custom_id == f"sell_role_select_{inter.author.id}" and i.author.id == inter.author.id,
                timeout=60
            )
        except TimeoutError:
            await inter.edit_original_response("Время выбора истекло!", view=None)
            return
        
        role_db_id = select_inter.values[0]
        role_info = roles_data[role_db_id]
        
        # Проверка, что роль все еще принадлежит пользователю
        if role_info.get("owner_id") != inter.author.id:
            await select_inter.response.send_message("Эта роль больше не принадлежит тебе!", ephemeral=True)
            return
        
        # Проверка, что роль уже не на рынке
        market_data = await get_market_data()
        for item_id, item in market_data.items():
            if item_id == "_id":
                continue
            if item["role_id"] == role_db_id:
                await select_inter.response.send_message("Эта роль уже выставлена на продажу!", ephemeral=True)
                return
        
        # Добавление роли на рынок
        market_item_id = str(len([k for k in market_data.keys() if k != "_id"]) + 1)
        market_data[market_item_id] = {
            "role_id": role_db_id,
            "price": цена,
            "seller_id": inter.author.id,
            "listed_at": disnake.utils.utcnow().isoformat(),
            "guild_id": role_info["guild_id"],
            "role_name": role_info["name"]
        }
        
        await update_market_data(market_data)
        
        guild = self.bot.get_guild(role_info["guild_id"])
        role = guild.get_role(role_info["role_id"]) if guild else None
        
        if role:
            await select_inter.response.send_message(
                f"Роль {role.mention} выставлена на продажу за {цена} монет! (ID товара: {market_item_id})",
                ephemeral=True
            )
        else:
            await select_inter.response.send_message(
                f"Роль '{role_info['name']}' выставлена на продажу за {цена} монет! (ID товара: {market_item_id})",
                ephemeral=True
            )

    @commands.slash_command(name="market", description="Посмотреть список ролей на рынке")
    async def market_list(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        
        market_data = await get_market_data()
        roles_data = await get_roles_data()
        
        # Убираем системное поле _id
        market_items = {k: v for k, v in market_data.items() if k != "_id"}
        
        if not market_items:
            await inter.edit_original_response("На рынке пока нет ролей!")
            return
        
        embed = disnake.Embed(
            title="🏪 Магазин ролей",
            description="Список доступных ролей для покупки",
            color=disnake.Color.gold()
        )
        
        for item_id, item in market_items.items():
            # Проверяем, что item - это словарь, а не строка
            if isinstance(item, dict) and "role_id" in item:
                role_db_id = item["role_id"]
                
                # Проверяем, что роль существует в базе
                if role_db_id in roles_data and role_db_id != "_id":
                    role_info = roles_data[role_db_id]
                    
                    # Получаем информацию о продавце
                    seller_id = item.get("seller_id")
                    if seller_id:
                        try:
                            seller = self.bot.get_user(seller_id) or await self.bot.fetch_user(seller_id)
                            seller_name = seller.mention
                        except:
                            seller_name = f"Неизвестный пользователь ({seller_id})"
                    else:
                        seller_name = "Неизвестный продавец"
                    
                    # Получаем информацию о роли на сервере
                    guild = self.bot.get_guild(role_info.get("guild_id"))
                    role = None
                    if guild:
                        role = guild.get_role(role_info.get("role_id"))
                    
                    role_name = role.mention if role else role_info.get("name", "Неизвестная роль")
                    price = item.get("price", 0)
                    
                    embed.add_field(
                        name=f"ID: {item_id} - {role_info.get('name', 'Неизвестная роль')}",
                        value=f"Цена: {price} монет\nПродавец: {seller_name}\nРоль: {role_name}",
                        inline=False
                    )
                else:
                    # Если роль не найдена, показываем базовую информацию
                    embed.add_field(
                        name=f"#{item_id} - Удаленная роль",
                        value=f"Цена: {item.get('price', 0)} монет\nРоль больше не существует",
                        inline=False
                    )
            else:
                # Пропускаем некорректные записи
                continue
        
        if len(embed.fields) == 0:
            await inter.edit_original_response("Нет доступных ролей для покупки!")
            return
        
        await inter.edit_original_response(embed=embed)

    @commands.slash_command(name="buy", description="Купить роль с рынка")
    async def buy_role(self, inter: disnake.ApplicationCommandInteraction, 
                    товар: str):
        """
        Parameters
        ----------
        товар: ID товара на рынке
        """
        await inter.response.defer()
        
        # Получение данных
        market_data = await get_market_data()
        roles_data = await get_roles_data()
        user_data = await get_user_data(inter.author.id)
        
        # Убираем системное поле _id
        market_items = {k: v for k, v in market_data.items() if k != "_id"}
        
        # Проверка существования товара
        if товар not in market_items:
            await inter.edit_original_response("Товар не найден!")
            return
        
        item = market_items[товар]
        
        # Проверяем, что item - словарь
        if not isinstance(item, dict) or "role_id" not in item:
            await inter.edit_original_response("Ошибка данных товара!")
            return
            
        # Проверка существования роли
        role_db_id = item["role_id"]
        if role_db_id not in roles_data or role_db_id == "_id":
            await inter.edit_original_response("Роль не найдена в базе данных!")
            return
                
        role_info = roles_data[role_db_id]
        
        # Проверка баланса
        price = item.get("price", 0)
        if user_data["wallet"] < price:
            await inter.edit_original_response(f"Недостаточно монет! Нужно {price}")
            return
        
        # Проверка, что покупатель не продавец
        if item.get("seller_id") == inter.author.id:
            await inter.edit_original_response("Нельзя купить свою же роль!")
            return
        
        # Получение роли
        guild = self.bot.get_guild(role_info.get("guild_id"))
        if not guild:
            await inter.edit_original_response("Сервер роли не найден!")
            return
            
        role = guild.get_role(role_info.get("role_id"))
        if not role:
            await inter.edit_original_response("Роль не найдена на сервере!")
            return
        
        # Выдача роли и перевод денег
        try:
            # Выдача роли покупателю
            await inter.author.add_roles(role)
            
            # Перевод денег продавцу
            seller_id = item.get("seller_id")
            if seller_id:
                seller_data = await get_user_data(seller_id)
                seller_data["wallet"] += price
                await update_user_data(seller_id, seller_data)
            
            # Списание денег у покупателя
            user_data["wallet"] -= price
            await update_user_data(inter.author.id, user_data)
            
            # Уведомление
            if seller_id:
                seller = self.bot.get_user(seller_id) or await self.bot.fetch_user(seller_id)
                seller_mention = seller.mention
            else:
                seller_mention = "Неизвестный продавец"
                
            await inter.edit_original_response(f"Ты успешно купил роль {role.mention} за {price} монет! Деньги переведены {seller_mention}")
            
        except Exception as e:
            await inter.edit_original_response(f"Ошибка при покупке: {e}")

    async def parse_color(self, color_str: str):
        """Преобразует строку цвета в объект Color"""
        color_str = color_str.lower().strip()
        
        # Проверка базовых цветов
        if color_str in self.color_map:
            return self.color_map[color_str]
        
        # Проверка HEX кода
        if re.match(r'^#?[0-9A-Fa-f]{6}$', color_str):
            if color_str.startswith('#'):
                hex_code = color_str[1:]
            else:
                hex_code = color_str
            
            try:
                return disnake.Color(int(hex_code, 16))
            except ValueError:
                return None
        
        return None

def setup(bot):
    bot.add_cog(RoleShop(bot))