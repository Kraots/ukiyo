from __future__ import annotations

import re
import math
import base64
import asyncio
import binascii
import functools
import string as st
from typing import Callable

import disnake
from disnake.ext import commands
from .constants import *

import utils

__all__ = (
    'time_phaser',
    'clean_code',
    'check_profanity',
    'check_string',
    'check_username',
    'run_in_executor',
    'clean_inter_content',
    'fail_embed',
    'format_amount',
    'escape_markdown',
    'remove_markdown',
    'CooldownByContentChannel',
    'CooldownByContentUser',
    'validate_token',
    'try_delete',
    'try_dm',
    'remove_zalgos',
    'send_embeds',
    'format_position',
    'TimeConverter',
    'natural_size'
)


def time_phaser(seconds, *, brief: bool = False, no_unit: bool = False, colon: bool = False):
    output = []
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    mo, d = divmod(d, 30)
    if mo > 0:
        output.append(str(int(round(m, 0))) + ("" if no_unit else " months " if not brief else "mo"))
    if d > 0:
        output.append(str(int(round(d, 0))) + ("" if no_unit else " days " if not brief else "d"))
    if h > 0:
        output.append(str(int(round(h, 0))) + ("" if no_unit else " hours " if not brief else "h"))
    if m > 0:
        output.append(str(int(round(m, 0))) + ("" if no_unit else " minutes " if not brief else "m"))
    if s > 0:
        output.append(str(int(round(s, 0))) + ("" if no_unit else " seconds" if not brief else "s"))

    return ':'.join(output) if colon else ''.join(output)


def clean_code(content):
    if content.startswith("```") and content.endswith("```"):
        return "\n".join(content.split("\n")[1:])[:-3]
    else:
        return content


def remove_zalgos(string: str, *, remove_whitespace: bool = False) -> str:
    """Return a string with every zalgo character removed.

    Parameters
    ----------
        string: :class:`str`
            The string to remove zalgo from.

        remove_whitespace: :class:`bool`
            Whether to also remove any whitespace/newline character or not.

    Return
    ------
        The new string with the removed zalgos.
    """

    _string = string
    string = ''

    for letter in _string:
        if letter in ALLOWED_CHARACTERS:
            if remove_whitespace is True:
                if letter not in st.whitespace:
                    string += letter
            else:
                string += letter

    return string


def check_profanity(string: str, *, bad_words: list, lazy: bool = True) -> bool:
    """
    If the return type is of bool ``True`` then it means that the
    string contains a bad word, otherwise ``False`` if it's safe.

    Parameters
    ----------
        string: :class:`str`
            The string to check if it contains a bad word.

        bad_words: :class:`list`
            A list of the bad words to check for.

        lazy: :class:`bool`
            If ``False``, this will return the word that triggered the filter along with the bool and the changed sentence
            in a tuple. If ``True`` it will only return the bool if the filter was triggered or not. Defaults to ``True``.

    Return
    ------
        True | False | tuple[bool, str]
    """

    bad_words = bad_words
    string = str(string).lower()

    if lazy is True:
        res = any(w for w in bad_words if w in string)
        if res is False:
            string = string.translate(EDGE_CHARACTERS_TABLE)  # Replace each edge character to its corresponding letter.
            string = string.replace('()', 'o')  # Replace this manually because ``str.maketrans`` keys must be of lenght 1.
            res = any(w for w in bad_words if w in string)

            if res is False:
                string = string.translate(EMOJIS_TABLE)  # Change every regional indicator emoji to its corresponding letter.
                for original, emoji in NUMBERS_EMOJI.items():
                    string.replace(emoji, original)  # Replace every number emoji with its corresponding number.
                res = any(w for w in bad_words if w in string)

                if res is False:
                    string = string.translate(PAD_TABLE)  # Remove every punctuation and digit character.
                    string = remove_zalgos(string, remove_whitespace=True)  # Remove any zalgo or non-abcd... character.
                    res = any(w for w in bad_words if w in string)

    else:
        def filter_word(string: str):
            for word in bad_words:
                if word in string:
                    start = string.index(word)
                    end = start + len(word)
                    new_word = '**`     ' + string[start:end] + '     `**'
                    string = string.replace(word, new_word)
                    return (True, word, string)
            return (False, '', string)

        res = filter_word(string)
        if res[0] is False:
            string = string.translate(EDGE_CHARACTERS_TABLE)  # Replace each edge character to its corresponding letter.
            string = string.replace('()', 'o')  # Replace this manually because ``str.maketrans`` keys must be of lenght 1.
            res = filter_word(string)

            if res[0] is False:
                string = string.translate(EMOJIS_TABLE)  # Change every regional indicator emoji to its corresponding letter.
                for original, emoji in NUMBERS_EMOJI.items():
                    string.replace(emoji, original)  # Replace every number emoji with its corresponding number.
                res = filter_word(string)

                if res[0] is False:
                    string = string.translate(PAD_TABLE)  # Remove every punctuation and digit character.
                    string = remove_zalgos(string, remove_whitespace=True)  # Remove any zalgo or non-abcd... character
                    res = filter_word(string)

    return res


def check_string(string: str, *, limit: str = 4, ignore_whitespace: bool = False) -> bool:
    """
    If the return type of bool is ``True`` then it means that the word has
    less allowed characters in a row than the limit, otherwise ``False``
    if the string meets the required limit.

    Parameters
    ----------
        string: :class:`str`
            The string to check if it has enough allowed characters in a row.

        limit: :class:`int`
            The limit for which to check the lenght of the allowed letters in a row within the string.
            Defaults to 4.

        ignore_whitespace: :class:`bool`
            Whether to ignore any whitespace characters or not.

    Return
    ------
        True | False
    """

    if ignore_whitespace is True:
        string = string.replace(' ', '').replace('\n', '')

    count = 0
    for letter in string:
        if count < limit:
            if letter not in ALLOWED_CHARACTERS:
                count = 0
            else:
                count += 1
        else:
            break

    return count < limit


async def check_username(bot, member: disnake.Member, *, bad_words: list):
    """
    Check the ``member``'s display name, if all the checks pass,
    he's ignored, otherwise, his nickname gets changed.

    Parameters
    ----------
        member: :class:`disnake.Member`
            The member to check if their display name is shorter
            than ``limit`` and if they have any bad word in it.
    """

    if member.id == bot._owner_id or member.bot:
        return
    name = member.display_name.lower()
    res = check_string(name, ignore_whitespace=True) or check_profanity(name, bad_words=bad_words)
    if res is False:
        return

    entry: utils.Misc = await bot.db.get('misc')
    entry.invalidnames += 1
    await entry.commit()
    new_nick = f'UnpingableName{entry.invalidnames}'
    await member.edit(nick=new_nick, reason='username not pingable, is a bad word or is too short')
    try:
        return await member.send(
            'Your name has too few pingable letters in a row, '
            f'is a bad word or is too short (minimum is **4**) so I changed it to `{new_nick}`\n'
        )
    except disnake.Forbidden:
        return


def run_in_executor(func: Callable):
    """Decorator that runs the sync function in the executor."""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        to_run = functools.partial(func, *args, **kwargs)
        return await loop.run_in_executor(None, to_run)

    return wrapper


def clean_inter_content(
    *,
    fix_channel_mentions: bool = False,
    use_nicknames: bool = True,
    escape_markdown: bool = False,
    remove_markdown: bool = False,
):
    async def convert(inter: disnake.ApplicationCommandInteraction, argument: str):
        if inter.guild:
            def resolve_member(id: int) -> str:
                m = inter.guild.get_member(id)
                return f'@{m.display_name if use_nicknames else m.name}' if m else '@deleted-user'

            def resolve_role(id: int) -> str:
                r = inter.guild.get_role(id)
                return f'@{r.name}' if r else '@deleted-role'
        else:
            def resolve_member(id: int) -> str:
                m = inter.bot.get_user(id)
                return f'@{m.name}' if m else '@deleted-user'

            def resolve_role(id: int) -> str:
                return '@deleted-role'

        if fix_channel_mentions and inter.guild:
            def resolve_channel(id: int) -> str:
                c = inter.guild.get_channel(id)
                return f'#{c.name}' if c else '#deleted-channel'
        else:
            def resolve_channel(id: int) -> str:
                return f'<#{id}>'

        transforms = {
            '@': resolve_member,
            '@!': resolve_member,
            '#': resolve_channel,
            '@&': resolve_role,
        }

        def repl(match: re.Match) -> str:
            type = match[1]
            id = int(match[2])
            transformed = transforms[type](id)
            return transformed

        result = re.sub(r'<(@[!&]?|#)([0-9]{15,20})>', repl, argument)
        if escape_markdown:
            result = disnake.utils.escape_markdown(result)
        elif remove_markdown:
            result = disnake.utils.remove_markdown(result)

        # Completely ensure no mentions escape:
        return disnake.utils.escape_mentions(result)

    return convert


def fail_embed(description: str) -> disnake.Embed:
    return disnake.Embed(title='Uh-oh!', color=utils.red, description=description)


def format_amount(num: str) -> str:
    return num \
        .replace(',', '') \
        .replace(' ', '') \
        .replace('.', '')


def escape_markdown(text: str) -> str:
    r"""Escapes the markdown from the text. That means **hello** becomes \\*\\*hello\\*\\*

    Parameters
    ----------
        text: :class:`str`
            The text to escape the markdown from.

    Return
    ------
        :class:`str`
            The new string with the escaped markdown.
    """

    return disnake.utils.escape_markdown(text)


def remove_markdown(text: str) -> str:
    r"""Removes the markdown from the text. That means **hello** becomes hello

    Parameters
    ----------
        text: :class:`str`
            The text to remove the markdown from.

    Return
    ------
        :class:`str`
            The new string with the removed markdown.
    """

    return disnake.utils.remove_markdown(text)


class CooldownByContentChannel(commands.CooldownMapping):
    def _bucket_key(ctx, message):
        content = message.content.lower()
        if not content:
            content = message.attachments[0].url if message.attachments else ''
        return (message.channel.id, content)


class CooldownByContentUser(commands.CooldownMapping):
    def _bucket_key(ctx, message):
        content = message.content.lower()
        if not content:
            content = message.attachments[0].url if message.attachments else ''
        return (message.author.id, content)


def validate_token(token):
    try:
        # Just check if the first part validates as a user ID
        (user_id, _, _) = token.split('.')
        user_id = int(base64.b64decode(user_id, validate=True))
    except (ValueError, binascii.Error):
        return False
    else:
        return True


async def try_delete(
    message: disnake.Message | list[disnake.Message] | tuple[disnake.Message] | set[disnake.Message] = None,
    *,
    channel: disnake.TextChannel | disnake.Thread = None,
    message_id: int | list[int] | tuple[int] | set[int] = None,
    delay: float | int = None
):
    """|coro|

    A helper function that tries to delete a :class:`disnake.Message` object
    while silencing the errors that it may raise.

    Parameters
    ----------
        message: Optional[:class:`disnake.Message` | list[:class:`disnake.Message`] |
        tuple[:class:`disnake.Message`] | set[:class:`disnake.Message`]]
            The message to try and delete, can also be a list of message objects.
            If `channel` and `message_id` is not given, this is required.

        channel: Optional[:class:`disnake.TextChannel` | :class:`disnake.Thread`]
            The channel from which to fetch the message object. If this is given, `message_id` becomes required.
            This gets ignored if `message` is not ``None``.

        message_id: Optional[:class:`int` | list[:class:`int`] | tuple[:class:`int`] | set[:class:`int`]]
            The message id for the message object to fetch, can also be a list of message ids.
            If this is given, `channel` becomes required. This gets ignored if `message` is not ``None``.

        delay: Optional[:class:`float` | :class:`int`]
            The time to wait in the background before deleting the message.

    Raises
    ------
        :class:`TypeError` if the type of an argument or key-word argument isn't any of the required ones.

    Return
    -------
        ``None``
    """

    if message is None and channel is None and message_id is None:
        return

    elif delay is not None and not isinstance(delay, (float, int)):
        raise TypeError(
            "Argument 'delay' must be of type 'float' or 'int', "
            f"not {delay.__class__}"
        )

    if message is not None:
        if isinstance(message, disnake.Message):
            try:
                await message.delete(delay=delay)
            except disnake.HTTPException:
                return

        elif isinstance(message, (list, tuple, set)):
            for i, message in enumerate(message):
                if not isinstance(message, disnake.Message):
                    raise TypeError(
                        f"Expected value at index '{i}' in 'message' to be of type 'disnake.Message', "
                        f"not {message.__class__}"
                    )

                try:
                    await message.delete(delay=delay)
                except disnake.HTTPException:
                    pass

        else:
            raise TypeError(
                "Argument 'message' must be of type 'disnake.Message', 'list[disnake.Message]', "
                f"'tuple[disnake.Message]' or 'set[disnake.Message]', not {message.__class__}"
            )
        return

    if channel is not None and message_id is None:
        raise utils.MissingArgument(
            "If 'channel' is given, 'message_id' is required!"
        )

    elif message_id is not None and channel is None:
        raise utils.MissingArgument(
            "If 'message_id' is given, 'channel' is required!"
        )

    else:
        if not isinstance(channel, (disnake.TextChannel, disnake.Thread)):
            raise TypeError(
                "Argument 'channel_id' must be of type 'disnake.TextChannel' or 'disnake.Thread', "
                f"not {channel.__class__}"
            )

        if isinstance(message_id, int):
            try:
                message = await channel.fetch_message(message_id)
                await message.delete(delay=delay)
            except disnake.HTTPException:
                return

        elif isinstance(message_id, (list, tuple, set)):
            for i, mid in enumerate(message_id):
                if not isinstance(mid, int):
                    raise TypeError(
                        f"Expected value at index '{i}' in 'message_id' to be of type 'int', "
                        f"not {message.__class__}"
                    )
                try:
                    message = await channel.fetch_message(mid)
                    await message.delete(delay=delay)
                except disnake.HTTPException:
                    pass
            return

        else:
            raise TypeError(
                "Argument 'message_id' must be of type 'int', 'list[int]', "
                f"'tuple[int]' or 'set[int]' not {message_id.__class__}"
            )


async def try_dm(
    user: disnake.Member | disnake.User | list[disnake.Member | disnake.User] |
    tuple[disnake.Member | disnake.User] | set[disnake.Member | disnake.User],
    *args,
    **kwargs
):
    """|coro|

    Try to dm a user or multiple users the same message while silencing whatever error it may raise.

    Parameters
    ----------
        user: :class:`disnake.Member` | :class:`disnake.User` |
        list[:class:`disnake.Member` | :class:`disnake.User`] |
        tuple[:class:`disnake.Member` | :class:`disnake.User`] |
        set[:class:`disnake.Member` | :class:`disnake.User`]
            The user(s) to dm.

        *args: The args of every ``.send`` method.
        **kwargs: The kwargs of every ``.send`` method.

    Raises
    ------
        :class:`TypeError` if the user isn't a Member or a User object, or a list, tuple or set of those two.

    Return
    ------
        ``None``
    """

    if isinstance(user, (disnake.Member, disnake.User)):
        try:
            await user.send(*args, **kwargs)
        except disnake.HTTPException:
            return

    elif isinstance(user, (list, tuple, set)):
        for i, usr in enumerate(user):
            if not isinstance(usr, (disnake.Member, disnake.User)):
                raise TypeError(
                    f"Expected value at index '{i}' in 'usr' to be of type "
                    f"'disnake.Member' or 'disnake.User', not {usr.__class__}"
                )

            try:
                await usr.send(*args, **kwargs)
            except disnake.HTTPException:
                pass
        return

    else:
        raise TypeError(
            "Argument 'user' must be of type 'disnake.Member', 'disnake.User', "
            "'list[disnake.Member | disnake.User]', 'tuple[disnake.Member | disnake.User]' or "
            f"'set[disnake.Member | disnake.User]' not {user.__class__}"
        )


async def send_embeds(
    destination: disnake.TextChannel | disnake.Webhook | disnake.Thread | disnake.User | disnake.Member,
    embeds: list[disnake.Embed] | tuple[disnake.Embed] | set[disnake.Embed]
):
    """
    Safe sends the embeds to the destination.

    Parameters
    ----------
        destination: :class:`disnake.TextChannel` | :class:`disnake.Webhook`
        :class:`disnake.Thread` | :class:`disnake.User` | :class:`disnake.Member`
            The destination where to send the embeds to.

        embeds: list[:class:`disnake.Embed`] | tuple[:class:`disnake.Embed`]
        | set[:class:`disnake.Embed`]
            The embeds to send.

    Return
    ------
        ``None``
    """

    if not isinstance(
        destination,
        (
            disnake.TextChannel, disnake.Webhook,
            disnake.Thread, disnake.User, disnake.Member
        )
    ):
        raise TypeError(
            "Argument 'destination' must be of type 'disnake.TextChannel', 'disnake.Webhook', "
            "'disnake.Thread', 'disnake.User' or 'disnake.Member', "
            f"not {destination.__class__}"
        )

    elif not isinstance(embeds, (list, tuple, set)):
        raise TypeError(
            "Argument 'embeds' must be of type 'list[disnake.Embed]', 'tuple[disnake.Embed]', "
            f"or 'set[disnake.Embed]', not {embeds.__class__}"
        )

    if len(embeds) == 1:
        await destination.send(embed=embeds[0])
    elif len(embeds) > 1:
        count = 0
        ems = []
        for em in embeds:
            ems.append(em)
            count += 1
            if count == 10:
                await destination.send(embeds=ems)
                count = 0
                ems = []
        else:
            if count != 0:
                await destination.send(embeds=ems)
                ems = []


def format_position(n: int | str) -> str:
    """Adds st|nd|th correspondingly.

    Parameters
    ----------
        n: :class:`int` | :class:`str`
            The number to format.

    Return
    ------
        :class:`str`
            The formatted number.
    """

    if isinstance(n, int):
        n = f'{n:,}'
    else:
        n = int(n)
        n = f'{n:,}'

    if n.endswith('1') and not n.endswith('11'):
        return n + 'st'
    elif n.endswith('2') and not n.endswith('12'):
        return n + 'nd'
    elif n.endswith('3') and not n.endswith('13'):
        return n + 'rd'
    else:
        return n + 'th'


time_regex = re.compile(r"(?:(\d{1,5})(h|s|m|d))+?")
time_dict = {"h": 3600, "s": 1, "m": 60, "d": 86400}


class TimeConverter():
    @classmethod
    async def convert(self, argument):
        args = argument.lower()
        matches = re.findall(time_regex, args)
        time = 0
        for v, k in matches:
            try:
                time += time_dict[k] * float(v)
            except KeyError:
                raise commands.BadArgument(f"{k} is an invalid time-key! h/m/s/d are valid!")
            except ValueError:
                raise commands.BadArgument(f"{v} is not a number!")
        return time


def natural_size(size_in_bytes: int):
    """
    Converts a number of bytes to an appropriately-scaled unit
    E.g.:
        1024 -> 1.00 KiB
        12345678 -> 11.77 MiB
    """
    units = ('B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB')

    power = int(math.log(size_in_bytes, 1024))

    return f"{size_in_bytes / (1024 ** power):.2f} {units[power]}"