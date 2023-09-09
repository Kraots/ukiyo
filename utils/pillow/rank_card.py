from io import BytesIO

from PIL import Image, ImageFont, ImageDraw

import disnake

import utils

GRAY = (48, 48, 48)
ORANGE = (255, 128, 0)
TRANSPARENT = (0, 0, 0, 0)
BLUE = (22, 160, 245)
BLACK = (0, 0, 0)
TTF_FONT = './assets/Milliard.otf'

__all__ = ('create_rank_card',)


@utils.run_in_executor
def draw_progress_bar(d, x, y, w, h, progress, bg="white", fg="black"):
    # draw background
    d.ellipse((x + w, y, x + h + w, y + h), fill=bg)
    d.ellipse((x, y, x + h, y + h), fill=bg)
    d.rectangle((x + (h / 2), y, x + w + (h / 2), y + h), fill=bg)

    # draw progress bar
    w *= progress
    if w != 0.0:
        d.ellipse((x + w, y, x + h + w, y + h), fill=fg)
        d.ellipse((x, y, x + h, y + h), fill=fg)
        d.rectangle((x + (h / 2), y, x + w + (h / 2), y + h), fill=fg)

    return d


@utils.run_in_executor
def get_font(text, image):
    fontsize = 1
    font = ImageFont.truetype(TTF_FONT, fontsize)
    while font.getsize(text)[0] < image.size[0]:
        fontsize += 1
        font = ImageFont.truetype(TTF_FONT, fontsize)
    while font.getsize(text)[1] > image.size[1]:
        fontsize -= 1
        font = ImageFont.truetype(TTF_FONT, fontsize)
    fontsize -= 1
    font = ImageFont.truetype(TTF_FONT, fontsize)
    return font


async def create_rank_card(
    user: disnake.Member,
    level: int,
    rank: int,
    members_count: int,
    current_xp: int,
    needed_xp: int,
    percentage: float
):
    img = await utils.run_in_executor(Image.new)("RGBA", (1000, 350), GRAY)

    av = await utils.run_in_executor(Image.open)(BytesIO(await user.display_avatar.read()))

    orange_line = await utils.run_in_executor(Image.new)("RGBA", (500, 10), ORANGE)

    _user = await utils.run_in_executor(Image.new)("RGBA", (500, 50), TRANSPARENT)
    draw = await utils.run_in_executor(ImageDraw.Draw)(_user)
    txt = user.display_name
    font = await get_font(txt, _user)
    await utils.run_in_executor(draw.text)((0, 0), txt, font=font)

    has_xp = await utils.run_in_executor(Image.new)("RGBA", (200, 40), TRANSPARENT)
    draw = await utils.run_in_executor(ImageDraw.Draw)(has_xp)
    font = ImageFont.truetype(TTF_FONT, 35)
    await utils.run_in_executor(draw.text)((0, 0), f"{current_xp:,}xp", font=font, fill=BLACK)

    percent = await utils.run_in_executor(Image.new)("RGBA", (140, 40), TRANSPARENT)
    draw = await utils.run_in_executor(ImageDraw.Draw)(percent)
    font = ImageFont.truetype(TTF_FONT, 35)
    await utils.run_in_executor(draw.text)((10, 0), f"{percentage}%", font=font, fill=BLACK)

    next_xp = await utils.run_in_executor(Image.new)("RGBA", (200, 40), TRANSPARENT)
    draw = await utils.run_in_executor(ImageDraw.Draw)(next_xp)
    font = ImageFont.truetype(TTF_FONT, 35)
    if len(str(needed_xp)) == 3:
        z = f"    {needed_xp:,}xp"
    else:
        z = f"{needed_xp:,}xp"
    await utils.run_in_executor(draw.text)((0, 0), z, font=font, fill=BLACK)

    progressbar = await utils.run_in_executor(Image.new)("RGBA", (750, 50), (0, 0, 0, 0))
    d = await utils.run_in_executor(ImageDraw.Draw)(progressbar)
    d = await draw_progress_bar(d, 0, 0, 650, 45, percentage / 100, fg=BLUE)

    _rank = await utils.run_in_executor(Image.new)("RGBA", (235, 100))
    draw = await utils.run_in_executor(ImageDraw.Draw)(_rank)
    font = ImageFont.truetype(TTF_FONT, 35)
    await utils.run_in_executor(draw.text)((0, 0), f"     Rank:\n        {rank}/{members_count}", font=font)

    _level = await utils.run_in_executor(Image.new)("RGBA", (235, 100))
    draw = await utils.run_in_executor(ImageDraw.Draw)(_level)
    font = ImageFont.truetype(TTF_FONT, 35)
    await utils.run_in_executor(draw.text)((0, 0), f"     Level:\n        {level}", font=font)

    await utils.run_in_executor(utils.paste_rounded_image)(img, av, 250, (10, 50))
    await utils.run_in_executor(img.paste)(im=orange_line, box=(350, 100))
    await utils.run_in_executor(img.paste)(im=_user, mask=_user, box=(350, 50))
    await utils.run_in_executor(img.paste)(im=progressbar, mask=progressbar, box=(275, 250))
    await utils.run_in_executor(img.paste)(im=has_xp, mask=has_xp, box=(285, 260))
    await utils.run_in_executor(img.paste)(im=next_xp, mask=next_xp, box=(800, 260))
    await utils.run_in_executor(img.paste)(im=percent, mask=percent, box=(550, 260))
    await utils.run_in_executor(img.paste)(im=_rank, mask=_rank, box=(325, 125))
    await utils.run_in_executor(img.paste)(im=_level, mask=_level, box=(600, 125))
    await utils.run_in_executor(img.save)('rank_card.png')

    f = disnake.File(fp='rank_card.png', filename='rank_card.png')

    return f