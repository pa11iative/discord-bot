import disnake
from disnake.ext import commands

class WelcomeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.WELCOME_CHANNEL_ID = 1140243006860038166

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = self.bot.get_channel(self.WELCOME_CHANNEL_ID)
        if not channel:
            return
        
        # Создаем embed
        embed = disnake.Embed(
            description=f'''✧༺⚔︎༻✧ 𖤐 ✧༺⚔︎༻✧
𓆩ᥫ᭡𓆪         𖣘
      
welc . . . {member.mention} ✝ Born to die.

⇨ [guide](https://discord.com/channels/1140243005681455205/1393701383705985064)   ⛓ [giveaways](https://discord.com/channels/1140243005681455205/1389695940197355591) ☠︎ ~~~
⚘ [staff recruiting](https://discord.com/channels/1140243005681455205/1405148431621685318)     ༺✞༻

｡･::･ﾟ★,｡･::･ﾟ☆｡･::･ﾟ★,｡･::･ﾟ''',
            color=disnake.Color.green()  # Можно изменить цвет
        )
        
        # Добавляем изображение (замените URL на ваше изображение)
        embed.set_image(url="https://media.discordapp.net/attachments/1403639112636043304/1417078613454491748/3e3c1b07cbb1e21b117677e33736f4b5.jpg?ex=68c92ccd&is=68c7db4d&hm=97c259e34407aa7e257d1b393572d1ae91ed874c4ebf236e0fac3627a3078970&=&format=webp&width=1470&height=838")  # URL вашего изображения
        
        # Отправляем сообщение с упоминанием роли и embed
        await channel.send('<@&1412754553555648562>', embed=embed)

def setup(bot):
    bot.add_cog(WelcomeCog(bot))