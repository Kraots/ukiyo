from typing import Optional
from datetime import datetime, timezone

import disnake

import utils

__all__ = ('log',)


async def log(
    channel: disnake.TextChannel | disnake.Webhook,
    *,
    title: Optional[str] = None,
    description: Optional[str] = None,
    fields: Optional[list[tuple[str, str]]] = [],
    timestamp: Optional[bool] = False,
    view: Optional[disnake.ui.View] = None
) -> Optional[disnake.Message]:
    """
    A function that sends an embed to ``channel`` with the
    purpose to log an action.

    Parameters
    ----------
        channel: :class:`TextChannel` | :class:`Webhook`
            The channel to send the log to.
        title: Optional[:class:`str`]
            The title of the logging embed. Defaults to :class:``.EmptyEmbed``
        description: Optional[:class:`str`]
            The description of the logging embed. Defaults to :class:``.EmptyEmbed``
        fields: List[Tuple[:class:`str`, :class:`str`]]
            The fields to add to the embed, must be a list of tuples where each tuple
            is of ``3`` items, the first being the field's name, the second being
            the field's value and the third being a boolean for the inline kwarg which
            defaults to ``False``.
        timestamp: Optional[:class:`bool`]
            If set to ``True``, the footer will specify the date this got logged in.
            Defaults to ``False``.
        view: Optional[:class:`ui.View`]
            The view to attach to the log message.

    Returns
    -------
        If the channel is an instance of :class:`.TextChannel`,
        it will return the :class:``.Message`` instance that is sent.
        Otherwise if it's an instance of :class:`.Webhook`, it will return ``None``.
    """

    if not isinstance(channel, (disnake.TextChannel, disnake.Webhook)):
        raise TypeError(
            "Argument 'channel' must be of type 'disnake.TextChannel' or 'disnake.Webhook', "
            f"not {channel.__class__}"
        )
    elif not isinstance(title, (str, type(None))):
        raise TypeError(
            "Argument 'title' must be of type 'str' or 'None', "
            f"not {title.__class__}")
    elif not isinstance(description, (str, type(None))):
        raise TypeError(
            "Argument 'description' must be of type 'str' or 'None', "
            f"not {description.__class__}")
    elif not isinstance(fields, (list, tuple)):
        raise TypeError(
            "Argument 'fields' must be of type 'list', "
            f"not {fields.__class__}")
    elif not isinstance(timestamp, bool):
        raise TypeError(
            "Argument 'timestamp' must be of type 'bool', "
            f"not {timestamp.__class__}")
    elif not isinstance(view, (disnake.ui.View, type(None))):
        raise TypeError(
            "Argument 'view' must be of type 'disnake.ui.View', "
            f"not {view.__class__}")
    elif (
        (description is None) and
        (title is None)
    ):
        raise utils.MissingArgument(
            "'title' or 'description' not given. Please specify at least one of them."
        )
    if title is not None:
        title = f'`{title}`'

    em = disnake.Embed(
        title=title,
        description=description,
        color=utils.red
    )
    _field = -1
    for field in fields:
        _field += 1
        if not isinstance(field, tuple):
            raise TypeError(
                f"'field.{_field}' must be of type 'tuple', not {field.__class__}"
            )
        elif len(field) < 2 or len(field) > 3:
            raise utils.ExtraArgument(
                f"'field.{_field}' has less than 2 or more than 3 elements."
            )

        if len(field) == 2:
            inline = False
        else:
            inline = field[2]
        em.add_field(
            name=field[0],
            value=field[1],
            inline=inline
        )
    if timestamp is True:
        em.timestamp = datetime.now(timezone.utc)

    try:
        return await channel.send(embed=em, view=view)
    except AttributeError:
        pass  # Weirdly enough this gets raised but the embed still gets sent