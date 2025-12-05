from PIL import Image, ImageDraw, ImageFont
import aiohttp
import io
import disnake
from utils.database import clans

async def draw_text_centered(draw, text, position, font, fill_color):
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = position[0] - text_width // 2
    y = position[1] - text_height // 2
    draw.text((x, y), text, font=font, fill=fill_color)

async def add_progress_bar_to_xd(current, total, bar_coords, bar_size, colors, xd):
    draw = ImageDraw.Draw(xd)
    start_x, start_y = bar_coords
    bar_width, bar_height = bar_size
    progress_percent = current / total
    filled_width = int(bar_width * progress_percent)
    
    if filled_width > 0:
        draw.rectangle([start_x, start_y, start_x + filled_width, start_y + bar_height], fill=colors['filled'])
    if filled_width < bar_width:
        draw.rectangle([start_x + filled_width, start_y, start_x + bar_width, start_y + bar_height], fill=colors['empty'])
    if 'border' in colors:
        draw.rectangle([start_x - 1, start_y - 1, start_x + bar_width + 1, start_y + bar_height + 1], outline=colors['border'], width=2)
    
    return xd

async def generate_profile_card(user: disnake.Member, data: dict, bot) -> disnake.File:
    level = data.get("level", 1)
    exp = data.get("exp", 0)
    required = 100 + level * 20
    wallet = data.get("wallet", 0)
    messages = data.get("messages_sent", 0)
    voice = data.get("voice_time", 0)

    background = Image.open("assets/profile_background_cut.png").convert("RGBA")
    xd = Image.new('RGBA', (1280, 720), (0, 0, 0, 0))

    async with aiohttp.ClientSession() as session:
        async with session.get(user.display_avatar.url) as resp:
            avatar_bytes = await resp.read()
    avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA").resize((155,155))

    partner = int(data.get("marry", 0))
    partner_avatar = None
    partner_name = None
    
    if partner:
        qq = await bot.fetch_user(partner)
        async with aiohttp.ClientSession() as session:
            async with session.get(qq.display_avatar.url) as resp:
                if resp.status == 200:
                    avatar_bytes = await resp.read()
                    partner_avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA").resize((68, 68))
                    partner_name = qq.name

    mask = Image.new("L", avatar.size, 0)
    ImageDraw.Draw(mask).ellipse((0, 0, avatar.size[0], avatar.size[1]), fill=255)
    avatar.putalpha(mask)
    draw = ImageDraw.Draw(xd)

    gilroy30 = ImageFont.truetype("assets/gilroy-medium.ttf", 30)
    gilroy25 = ImageFont.truetype("assets/gilroy-medium.ttf", 25)
    semibold45 = ImageFont.truetype("assets/gilroy-semibold.ttf", 45)
    semibold15 = ImageFont.truetype("assets/gilroy-regular.ttf", 15)
    reg35 = ImageFont.truetype("assets/gilroy-regular.ttf", 35)

    xd.paste(avatar, (561,135), avatar)
    plus = Image.open("assets/none.png").convert("RGBA").resize((68,68))
    
    xd = await add_progress_bar_to_xd(
        current=exp,
        total=required,
        bar_coords=(158,530),
        bar_size=(964, 200),
        colors={
            'filled': (162,194,104,255),
            'empty': (43,43,43,255),
            'border': (0, 0, 0, 255)
        },
        xd=xd
    )

    if partner and partner_avatar:
        xd.paste(partner_avatar, (865, 319), partner_avatar)
    else:
        xd.paste(plus, (865, 319), plus)
        
    cla_data = await clans.find_one({"members": user.id})
    clan_name = cla_data.get("name") if cla_data else None
    
    if clan_name:
        clan_avatar = avatar.resize((68,68))
        xd.paste(clan_avatar, (865, 176), clan_avatar)
    else:
        xd.paste(plus, (865, 176), plus)

    xd.paste(background, (0,0), background)

    hours = voice // 60
    minutes = voice % 60
    voice_str = f'{hours}ч {minutes}м'

    draw.text((262,174), str(wallet), font=gilroy30, fill="white")
    draw.text((262,267), voice_str, font=gilroy30, fill="white")
    draw.text((262,362), str(messages), font=gilroy30, fill="white")
    
    draw.text((940,194), clan_name or 'Отсутств...', font=gilroy25, fill="white")
    draw.text((940,340), partner_name[:8] + '...' if partner_name and len(partner_name) > 8 else partner_name or 'Отсутств...', font=gilroy25, fill="white")
    
    nick = user.name[:9] + '...' if len(user.name) > 10 else user.name
    await draw_text_centered(draw, nick, (637,338), semibold45, (162,194,104))
    await draw_text_centered(draw, str(level), (637,520), semibold45, "white")
    
    draw.text((161,560), f'{exp} xp', font=semibold15, fill=(87,90,83))
    draw.text((1070,560), f'{required} xp', font=semibold15, fill=(87,90,83))
    
    stat = ''
    if user.activities:
        for activity in user.activities:
            if activity.type == disnake.ActivityType.custom:
                stat = activity.name
                break
    stat_display = stat[:15] + '...' if len(stat) > 15 else stat
    await draw_text_centered(draw, stat_display, (637,388), reg35, (90,108,59))    
    
    flowers = Image.open("assets/flower.png").convert("RGBA") 
    xd.paste(flowers, (0,0), flowers)
    
    buffer = io.BytesIO()
    xd.save(buffer, format="PNG")
    buffer.seek(0)
    return disnake.File(buffer, filename="profile.png")
