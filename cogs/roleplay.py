import disnake
from disnake.ext import commands
from config import EMBED_COLOR
import os
import random
import json
from utils.database import get_user_data, update_user_data

def load_guide_data():
    path = "data/roleplay.json"
    if not os.path.exists(path):
        return {}

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

class roleplay(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def setup(bot):
        bot.add_cog(roleplay(bot))

    @commands.slash_command(name="обнять", description="Обнять участника")
    async def hug(self, inter: disnake.AppCmdInter, member: disnake.Member):
        await inter.response.defer()
        data = await get_user_data(inter.author.id)
        if data["wallet"] < 10:
            await inter.send("У тебя недостаточно монет (нужно 10)!", ephemeral=True)
            return
        data["wallet"] -= 10
        await update_user_data(inter.author.id, data)
        if member.bot:
            await inter.send("Ты не можешь обнять бота", ephemeral=True)
            return
        embed = disnake.Embed(
            description=f"{inter.author.mention} обнял(а) {member.mention}",
            color=EMBED_COLOR)
        data = load_guide_data()
        randurl = random.choice(data.get("hug", []))
        embed.set_image(url=randurl)
        await inter.send(embed=embed)

    @commands.slash_command(name="поцеловать", description="Поцеловать участника")
    async def kiss(self, inter: disnake.AppCmdInter, member: disnake.Member):
        await inter.response.defer()
        data = await get_user_data(inter.author.id)
        if data["wallet"] < 10:
            await inter.send("У тебя недостаточно монет (нужно 10)!", ephemeral=True)
            return
        data["wallet"] -= 10
        await update_user_data(inter.author.id, data)
        if member.bot:
            await inter.send("Ты не можешь поцеловать бота", ephemeral=True)
            return
        embed = disnake.Embed(
            description=f"{inter.author.mention} поцеловал(а) {member.mention}",
            color=EMBED_COLOR)
        data = load_guide_data()
        randurl = random.choice(data.get("kiss", []))
        embed.set_image(url=randurl)
        await inter.send(embed=embed)

    @commands.slash_command(name="заплакать", description="Заплакать")
    async def cry(self, inter: disnake.AppCmdInter):
        await inter.response.defer()
        data = await get_user_data(inter.author.id)
        if data["wallet"] < 10:
            await inter.send("У тебя недостаточно монет (нужно 10)!", ephemeral=True)
            return
        data["wallet"] -= 10
        await update_user_data(inter.author.id, data)
        embed = disnake.Embed(
            description=f"{inter.author.mention} заплакал(а)",
            color=EMBED_COLOR)
        data = load_guide_data()
        randurl = random.choice(data.get("cry", []))
        embed.set_image(url=randurl)
        await inter.send(embed=embed)

    @commands.slash_command(name="взять", description="Взять за руку участника")
    async def hand(self, inter: disnake.AppCmdInter, member: disnake.Member):
        await inter.response.defer()
        data = await get_user_data(inter.author.id)
        if data["wallet"] < 10:
            await inter.send("У тебя недостаточно монет (нужно 10)!", ephemeral=True)
            return
        data["wallet"] -= 10
        await update_user_data(inter.author.id, data)
        if member.bot:
            await inter.send("Ты не можешь взять за руку бота", ephemeral=True)
            return
        embed = disnake.Embed(
            description=f"{inter.author.mention} взял(а) за руку {member.mention}",
            color=EMBED_COLOR)
        data = load_guide_data()
        randurl = random.choice(data.get("hand", []))
        embed.set_image(url=randurl)
        await inter.send(embed=embed)

    @commands.slash_command(name="танцевать", description="Потанцевать")
    async def dance(self, inter: disnake.AppCmdInter):
        await inter.response.defer()
        data = await get_user_data(inter.author.id)
        if data["wallet"] < 10:
            await inter.send("У тебя недостаточно монет (нужно 10)!", ephemeral=True)
            return
        data["wallet"] -= 10
        await update_user_data(inter.author.id, data)
        embed = disnake.Embed(
            description=f"{inter.author.mention} танцует",
            color=EMBED_COLOR)
        data = load_guide_data()
        randurl = random.choice(data.get("dance", []))
        embed.set_image(url=randurl)
        await inter.send(embed=embed)

    @commands.slash_command(name="погладить", description="Погладить участника")
    async def pet(self, inter: disnake.AppCmdInter, member: disnake.Member):
        await inter.response.defer()
        data = await get_user_data(inter.author.id)
        if data["wallet"] < 10:
            await inter.send("У тебя недостаточно монет (нужно 10)!", ephemeral=True)
            return
        data["wallet"] -= 10
        await update_user_data(inter.author.id, data)
        if member.bot:
            await inter.send("Ты не можешь погладить бота", ephemeral=True)
            return
        embed = disnake.Embed(
            description=f"{inter.author.mention} погладил(а) {member.mention}",
            color=EMBED_COLOR)
        data = load_guide_data()
        randurl = random.choice(data.get("pet", []))
        embed.set_image(url=randurl)
        await inter.send(embed=embed)

    @commands.slash_command(name="спать", description="поспать")
    async def sleep(self, inter: disnake.AppCmdInter):
        await inter.response.defer()
        data = await get_user_data(inter.author.id)
        if data["wallet"] < 10:
            await inter.send("У тебя недостаточно монет (нужно 10)!", ephemeral=True)
            return
        data["wallet"] -= 10
        await update_user_data(inter.author.id, data)
        embed = disnake.Embed(
            description=f"{inter.author.mention} заснул(а)",
            color=EMBED_COLOR)
        data = load_guide_data()
        randurl = random.choice(data.get("sleep", []))
        embed.set_image(url=randurl)
        await inter.send(embed=embed)

    @commands.slash_command(name="смущаться", description="Засмущаться")
    async def shy(self, inter: disnake.AppCmdInter):
        await inter.response.defer()
        data = await get_user_data(inter.author.id)
        if data["wallet"] < 10:
            await inter.send("У тебя недостаточно монет (нужно 10)!", ephemeral=True)
            return
        data["wallet"] -= 10
        await update_user_data(inter.author.id, data)
        embed = disnake.Embed(
            description=f"{inter.author.mention} смущается",
            color=EMBED_COLOR)
        data = load_guide_data()
        randurl = random.choice(data.get("shy", []))
        embed.set_image(url=randurl)
        await inter.send(embed=embed)

    @commands.slash_command(name="ударить", description="Ударить участника")
    async def punch(self, inter: disnake.AppCmdInter, member: disnake.Member):
        await inter.response.defer()
        data = await get_user_data(inter.author.id)
        if data["wallet"] < 10:
            await inter.send("У тебя недостаточно монет (нужно 10)!", ephemeral=True)
            return
        data["wallet"] -= 10
        await update_user_data(inter.author.id, data)
        if member.bot:
            await inter.send("Ты не можешь ударить бота", ephemeral=True)
            return
        embed = disnake.Embed(
            description=f"{inter.author.mention} ударил(а) {member.mention}",
            color=EMBED_COLOR)
        data = load_guide_data()
        randurl = random.choice(data.get("punch", []))
        embed.set_image(url=randurl)
        await inter.send(embed=embed)

    @commands.slash_command(name="закурить", description="Закурить")
    async def smoke(self, inter: disnake.AppCmdInter):
        await inter.response.defer()
        data = await get_user_data(inter.author.id)
        if data["wallet"] < 10:
            await inter.send("У тебя недостаточно монет (нужно 10)!", ephemeral=True)
            return
        data["wallet"] -= 10
        await update_user_data(inter.author.id, data)
        embed = disnake.Embed(
            description=f"{inter.author.mention} закурил(а)",
            color=EMBED_COLOR)
        data = load_guide_data()
        randurl = random.choice(data.get("smoke", []))
        embed.set_image(url=randurl)
        await inter.send(embed=embed)

    @commands.slash_command(name="флиртовать", description="Флиртовать с участником")
    async def flirt(self, inter: disnake.AppCmdInter, member: disnake.Member):
        await inter.response.defer()
        data = await get_user_data(inter.author.id)
        if data["wallet"] < 10:
            await inter.send("У тебя недостаточно монет (нужно 10)!", ephemeral=True)
            return
        data["wallet"] -= 10
        await update_user_data(inter.author.id, data)
        if member.bot:
            await inter.send("Ты не можешь флиртовать с ботом", ephemeral=True)
            return
        embed = disnake.Embed(
            description=f"{inter.author.mention} флиртует с {member.mention}",
            color=EMBED_COLOR)
        data = load_guide_data()
        randurl = random.choice(data.get("flirt", []))
        embed.set_image(url=randurl)
        await inter.send(embed=embed)

def setup(bot):
    bot.add_cog(roleplay(bot))