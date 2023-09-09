from typing import NamedTuple

import string as st
from datetime import datetime

__all__ = (
    'FIRST_JANUARY_1970',
    'ALLOWED_CHARACTERS',
    'EDGE_CHARACTERS_CASES',
    'EDGE_CHARACTERS_TABLE',
    'PUNCTUATIONS_AND_DIGITS',
    'PAD_TABLE',
    'LETTERS_EMOJI',
    'LETTERS_TABLE',
    'EMOJIS_TABLE',
    'NUMBERS_EMOJI',
    'NUMBERS_TABLE',
    'Channels',
    'StaffRoles',
    'ExtraRoles'
)

FIRST_JANUARY_1970 = datetime(1970, 1, 1, 0, 0, 0, 0)
ALLOWED_CHARACTERS = tuple(st.printable)
EDGE_CHARACTERS_CASES = {
    '@': 'a',
    '0': 'o',
    '1': 'i',
    '$': 's',
    '!': 'i',
    '9': 'g',
    '5': 's',
}
EDGE_CHARACTERS_TABLE = str.maketrans(EDGE_CHARACTERS_CASES)
PUNCTUATIONS_AND_DIGITS = tuple(list(st.punctuation) + list(st.digits))
PAD_TABLE = str.maketrans({k: '' for k in PUNCTUATIONS_AND_DIGITS})

LETTERS_EMOJI = {
    'a': '🇦', 'b': '🇧', 'c': '🇨', 'd': '🇩',
    'e': '🇪', 'f': '🇫', 'g': '🇬', 'h': '🇭',
    'i': '🇮', 'j': '🇯', 'k': '🇰', 'l': '🇱',
    'm': '🇲', 'n': '🇳', 'o': '🇴', 'p': '🇵',
    'q': '🇶', 'r': '🇷', 's': '🇸', 't': '🇹',
    'u': '🇺', 'v': '🇻', 'w': '🇼', 'x': '🇽',
    'y': '🇾', 'z': '🇿'
}
NUMBERS_EMOJI = {
    '0': '0️⃣', '1': '1️⃣', '2': '2️⃣', '3': '3️⃣',
    '4': '4️⃣', '5': '5️⃣', '6': '6️⃣', '7': '7️⃣',
    '8': '8️⃣', '9': '9️⃣'
}
LETTERS_TABLE = str.maketrans(LETTERS_EMOJI)
NUMBERS_TABLE = str.maketrans(NUMBERS_EMOJI)

EMOJIS_TABLE = str.maketrans({v: k for k, v in LETTERS_EMOJI.items()})


class Channels(NamedTuple):
    verify = 1137497235978981507

    boosts = 1137493942556962846
    rules = 1137493980121145354
    news = 1137494007874863215
    welcome = 1137494051181056144
    colours = 1137494101512691732
    roles = 1137494124119990394
    intros = 1137494137692766339
    birthdays = 1137494181607112785

    general = 1137494205548204143
    venting = 1137494219439751189

    bots = 1137494263811285082
    memes = 1137494279984521349
    shitpost = 1137494324213465229
    bump = 1137496903290982481

    selfies = 1137494343800848456
    photos = 1137494370598260756
    videos = 1137494397236293732
    animals = 1137494572075855874
    art = 1137494586026115132

    no_mic_chat = 1137494764141424830
    music_commands = 1137494783829495868

    staff_chat = 1137489770449223771
    bot_commands = 1137489789495562371

    logs = 1137490043792015501
    messages_logs = 1137490055569612882
    moderation_logs = 1137490073751928832
    github = 1137494920626700338
    discord_notifications = 1137495033600278548


class StaffRoles(NamedTuple):
    owner = 1131711260753399878
    admin = 1137486077473587340
    mod = 1137486090299789322

    all = (owner, admin, mod)


class ExtraRoles(NamedTuple):
    unverified = 1137487077529878638
    booster = 1150106381513400331
    bot = 1150105782742962256
    muted = 1137487082332377199
