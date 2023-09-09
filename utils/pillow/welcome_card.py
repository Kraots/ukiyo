from io import BytesIO

from PIL import Image, ImageDraw

import utils
from .rank_card import GRAY, TRANSPARENT, get_font

import disnake

WHITE = (255, 255, 255)

__all__ = ('create_welcome_card',)


async def create_welcome_card(member: disnake.Member, join_pos: str) -> disnake.File:
    img = await utils.run_in_executor(Image.new)("RGBA", (1000, 600), TRANSPARENT)
    av = await utils.run_in_executor(Image.open)(BytesIO(await member.display_avatar.read()))

    bg = await utils.run_in_executor(Image.new)("RGBA", (1000, 425), GRAY)
    await utils.run_in_executor(img.paste)(bg, (0, 175))

    welcome = await utils.run_in_executor(Image.new)("RGBA", (750, 150), TRANSPARENT)
    draw = await utils.run_in_executor(ImageDraw.Draw)(welcome)
    txt = f'Welcome {member.display_name}'
    font = await get_font(txt, welcome)
    await utils.run_in_executor(draw.text)((0, 0), txt, font=font)
    await utils.run_in_executor(img.paste)(welcome, (135, 300), welcome)

    pos = await utils.run_in_executor(Image.new)("RGBA", (900, 150), TRANSPARENT)
    draw = await utils.run_in_executor(ImageDraw.Draw)(pos)
    txt = f'You are our {utils.format_position(join_pos)} member'
    font = await get_font(txt, pos)
    await utils.run_in_executor(draw.text)((0, 0), txt, font=font)
    await utils.run_in_executor(img.paste)(pos, (50, 375), pos)

    acc_age = await utils.run_in_executor(Image.new)("RGBA", (700, 100), TRANSPARENT)
    draw = await utils.run_in_executor(ImageDraw.Draw)(acc_age)
    txt = 'Joined discord  ' + utils.human_timedelta(member.created_at)
    font = await get_font(txt, acc_age)
    await utils.run_in_executor(draw.text)((0, 0), txt, font=font)
    await utils.run_in_executor(img.paste)(acc_age, (150, 500), acc_age)

    await utils.run_in_executor(utils.paste_rounded_image)(img, av, 250, (370, 25))
    await utils.run_in_executor(img.save)(f'welcomes/welcome-{member.id}.png')
    f = disnake.File(fp=f'welcomes/welcome-{member.id}.png', filename=f'welcome-{member.id}.png')

    return f