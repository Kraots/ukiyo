from typing import Any

from PIL import Image, ImageDraw
from PIL.Image import Image as IM

__all__ = ('paste_rounded_image',)


def create_rounded_mask(diameter: int):
    mask = Image.new('L', (diameter,) * 2)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, diameter, diameter), fill=255)

    return mask


def paste_rounded_image(im: IM, image: IM, diameter: int = None, box: Any = None) -> None:
    """Pastes a rounded image on another image.

    Parameters
    ----------
        im: :class:`Image`
            The image to paste on.

        image: :class:`Image`
            The image to round and paste.

        diameter: :class:`int`
            The diameter/size to resize the image to.

        box: :class:`Any`
            The normal `box` parameter from `Image.paste`

    Return
    ------
        ``None``
    """

    diameter = diameter or image.size[0]
    mask = create_rounded_mask(diameter)

    image = image.resize((diameter,) * 2)
    im.paste(image, box, mask)