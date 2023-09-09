import re

__all__ = (
    'INVITE_REGEX',
    'LANGUAGE_REGEX',
    'TOKEN_REGEX',
    'UNICODE_REGEX',
    'CUSTOM_EMOJI_REGEX',
    'URL_REGEX'
)

INVITE_REGEX = re.compile(
    r"(?:discord(?:[\.,]|dot)gg|"  # Could be discord.gg/
    r"discord(?:[\.,]|dot)com(?:\/|slash)invite|"  # or discord.com/invite/
    r"discordapp(?:[\.,]|dot)com(?:\/|slash)invite|"  # or discordapp.com/invite/
    r"discord(?:[\.,]|dot)me|"  # or discord.me
    r"discord(?:[\.,]|dot)io"  # or discord.io.
    r")(?:[\/]|slash)"  # / or 'slash'
    r"([a-zA-Z0-9\-]+)",  # the invite code itself
    flags=re.IGNORECASE,
)

LANGUAGE_REGEX = re.compile(r"(\w*)\s*(?:```)(\w*)?([\s\S]*)(?:```$)")

TOKEN_REGEX = re.compile(r'[a-zA-Z0-9_-]{23,28}\.[a-zA-Z0-9_-]{6,7}\.[a-zA-Z0-9_-]{27}')

UNICODE_REGEX = re.compile(
    "(["
    "\U0001F1E0-\U0001F1FF"  # flags (iOS)
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F700-\U0001F77F"  # alchemical symbols
    "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
    "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
    "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
    "\U0001FA00-\U0001FA6F"  # Chess Symbols
    "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
    "\U00002702-\U000027B0"  # Dingbats
    "])"
)
CUSTOM_EMOJI_REGEX = re.compile(r'<?(?P<animated>a)?:?(?P<name>[A-Za-z0-9\_]+):(?P<id>[0-9]{13,20})>?')

URL_REGEX = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')