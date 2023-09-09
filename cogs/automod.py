import datetime

import disnake
from disnake.ext import commands

import utils
from utils import StaffRoles, ExtraRoles

from main import Ukiyo


class AutoMod(commands.Cog):
    def __init__(self, bot: Ukiyo):
        self.bot = bot

        # (messages, seconds, user/member/channel)
        self.messages_cooldown_user = utils.CooldownByContentUser.from_cooldown(
            6, 15.0, commands.BucketType.user)  # Checks for same content from the same user (9msg per 15s)
        self.messages_cooldown_channel = utils.CooldownByContentChannel.from_cooldown(
            17, 21.0, commands.BucketType.user)  # Checks for same content in the same channel (17msg per 21s)
        self.user_cooldown = commands.CooldownMapping.from_cooldown(
            10, 13.0, commands.BucketType.user)  # Checks for member spam (10msg per 13s)
        self.words_cooldown = commands.CooldownMapping.from_cooldown(
            3, 1800.0, commands.BucketType.user)  # Checks for bad words (3msg per 30m)
        self.invite_cooldown = commands.CooldownMapping.from_cooldown(
            2, 900.0, commands.BucketType.user)  # Checks for invites (2msg per 15m)
        self.newline_cooldown = commands.CooldownMapping.from_cooldown(
            3, 120.0, commands.BucketType.user)  # Checks for newlines in a message (3msg per 2m)
        self.mentions_cooldown = commands.CooldownMapping.from_cooldown(
            3, 60.0, commands.BucketType.user)  # Checks for the amount of mentions in a message (3msg per 1m)
        self.emojis_cooldown = commands.CooldownMapping.from_cooldown(
            3, 30.0, commands.BucketType.user)  # Checks for the amount of emojis in a message in a message (3msg per 30s)

    async def get_mute_time(self, user_id) -> str:
        data: utils.Mute = await self.bot.db.get('mute', user_id)
        if data is None:
            streak = 1
        else:
            streak = data.streak + 1

        if streak == 1:
            return '2hours'
        elif streak == 2:
            return '5hours'
        elif streak == 3:
            return '10hours'
        elif streak == 4:
            return '1days'
        elif streak == 5:
            return '14days'
        elif streak == 6:
            return '1month'
        else:
            return 'permanent'  # This shouldn't really even happen, but just in case it really gets that bad.

    async def apply_action(self, message: disnake.Message, reason: str):
        user = message.author
        time = await self.get_mute_time(user.id)
        if time == 'permanent':
            time = '999years'
        _data = await utils.UserFriendlyTime().convert(f'{time} {reason.title()}')
        duration = utils.human_timedelta(_data.dt, suffix=False)
        expiration_date = utils.format_dt(_data.dt, "F")

        guild = self.bot.get_guild(1131710408542146602)
        role = guild.get_role(ExtraRoles.muted)

        data_was_none = False
        data: utils.Mute = await self.bot.db.get('mutes', user.id)
        if data is None:
            data: utils.Mute = utils.Mute(
                id=user.id,
                muted_by=self.bot.user.id,
                muted_until=_data.dt,
                reason=_data.arg,
                duration=duration,
                filter=True,
                is_muted=True,
                streak=1
            )
            data_was_none = True
        else:
            data.muted_by = self.bot.user.id
            data.is_muted = True
            data.muted_until = _data.dt
            data.reason = _data.arg
            data.duration = duration
            data.streak += 1
            data.filter = True

        if data.streak == 7:
            data.permanent = True

        if StaffRoles.mod in (r.id for r in message.author.roles):  # Checks for mod
            data.is_mod = True
        new_roles = [role for role in user.roles
                        if role.id != StaffRoles.mod
                        ] + [role]
        await user.edit(roles=new_roles, reason=f'[AUTOMOD: {reason.upper()}]')

        if data.permanent is True:
            duration = 'PERMANENT'
            expiration_date = 'PERMANENT'

        em = disnake.Embed()
        em.title = f'You have been muted in `{guild.name}`'
        em.add_field(
            'Reason',
            _data.arg,
            inline=False
        )
        em.add_field(
            'Duration',
            duration,
            inline=False
        )
        em.add_field(
            'Expires On',
            expiration_date,
            inline=False
        )
        em.add_field(
            'Muted By',
            'Automod',
            inline=False
        )
        em.color = utils.red
        await utils.try_dm(user, embed=em)

        await message.channel.send(
            f'> ⚠️ **[AUTOMOD: {reason.upper()}]** {user.mention} has been muted '
            f'until {expiration_date} (`{duration}`)'
        )

        if data_was_none is True:
            await self.bot.db.add('mutes', data)
        else:
            await data.commit()

        await utils.log(
            self.bot.webhooks['mod_logs'],
            title=f'[AUTOMOD MUTE]',
            fields=[
                ('Member', f'{user.display_name} (`{user.id}`)'),
                ('Reason', reason.title()),
                ('Mute Duration', f'`{duration}`'),
                ('Expires At', expiration_date),
                ('By', f'{self.bot.user.mention} (`{self.bot.user.id}`)'),
                ('At', utils.format_dt(datetime.datetime.now(), 'F')),
            ]
        )

    async def anti_raid(self, message: disnake.Message):
        current = message.created_at.timestamp()

        content_bucket_user = self.messages_cooldown_user.get_bucket(message)
        if content_bucket_user.update_rate_limit(current):
            content_bucket_user.reset()
            return await self.apply_action(message, 'anti raid (repeated text)')

        content_bucket_channel = self.messages_cooldown_channel.get_bucket(message)
        if content_bucket_channel.update_rate_limit(current):
            content_bucket_channel.reset()
            return await self.apply_action(message, 'anti raid (repeated text)')

        user_bucket = self.user_cooldown.get_bucket(message)
        if user_bucket.update_rate_limit(current):
            user_bucket.reset()
            return await self.apply_action(message, 'anti raid (spam)')

        count = len(message.mentions)
        if count > 6:
            await utils.try_delete(message)

            words_bucket = self.newline_cooldown.get_bucket(message)
            if words_bucket.update_rate_limit(current):
                words_bucket.reset()
                return await self.apply_action(message, 'anti raid (too many mentions)')

    async def anti_bad_words(self, message: disnake.Message):
        current = message.created_at.timestamp()
        jump = message.jump_url
        author = message.author
        content = message.content

        if utils.check_profanity(content, bad_words=self.bot.bad_words.keys()):
            await utils.try_delete(message)

            trigger = utils.check_profanity(content, bad_words=self.bot.bad_words.keys(), lazy=False)
            await utils.log(
                self.bot.webhooks['mod_logs'],
                title='[BAD WORD DETECTED]',
                fields=[
                    ('Author', f'{author.display_name} (`{author.id}`)'),
                    ('Word', trigger[1]),
                    ('Detected In The Sentence', trigger[2]),
                    ('At', utils.format_dt(datetime.datetime.now(), 'F')),
                ],
                view=utils.UrlButton('Jump!', jump)
            )

            words_bucket = self.words_cooldown.get_bucket(message)
            if words_bucket.update_rate_limit(current):
                words_bucket.reset()
                return await self.apply_action(message, 'bad words')

    async def anti_invites(self, message: disnake.Message):
        current = message.created_at.timestamp()
        content = utils.remove_zalgos(message.content.replace(' ', '').replace('\\', ''))
        matches = utils.INVITE_REGEX.findall(content)
        if matches:
            guild = self.bot.get_guild(1131710408542146602)
            ukiyo_invites = [inv.code for inv in await guild.invites()]
            try:
                ukiyo_invites.append((await guild.vanity_invite()).code)
            except disnake.HTTPException:
                pass
            if any(inv for inv in matches if inv not in ukiyo_invites):
                await utils.try_delete(message)

                invite_bucket = self.invite_cooldown.get_bucket(message)
                if invite_bucket.update_rate_limit(current):
                    invite_bucket.reset()
                    return await self.apply_action(message, 'invite found')
                return

    async def anti_newlines(self, message: disnake.Message):
        current = message.created_at.timestamp()

        count = message.content.count('\n')
        if count > 15:
            await utils.try_delete(message)

            words_bucket = self.newline_cooldown.get_bucket(message)
            if words_bucket.update_rate_limit(current):
                words_bucket.reset()
                return await self.apply_action(message, 'too many lines')

    async def anti_emojis(self, message: disnake.Message):
        current = message.created_at.timestamp()

        unicode_emojis_count = len(utils.UNICODE_REGEX.findall(message.content))
        custom_emojis_count = len(utils.CUSTOM_EMOJI_REGEX.findall(message.content))
        total_emojis_count = unicode_emojis_count + custom_emojis_count
        if total_emojis_count > 15:
            await utils.try_delete(message)

            words_bucket = self.newline_cooldown.get_bucket(message)
            if words_bucket.update_rate_limit(current):
                words_bucket.reset()
                return await self.apply_action(message, 'too many emojis')

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.author.bot or message.author.id == self.bot._owner_id or\
                not message.guild or message.guild.id != 1131710408542146602 or \
                StaffRoles.admin in (r.id for r in message.author.roles) or \
                not message.content:
            return

        for coro in self.coros.copy():
            if await coro(self, message):
                break

    @commands.Cog.listener()
    async def on_message_edit(self, before: disnake.Message, after: disnake.Message):
        if after.author.bot or after.author.id == self.bot._owner_id or \
                not after.guild or after.guild.id != 1131710408542146602 or \
                StaffRoles.admin in (r.id for r in after.author.roles) or \
                not after.content:
            return

        for coro in self.coros.copy():
            if await coro(self, after):
                break

    coros = [anti_bad_words, anti_invites, anti_raid, anti_newlines, anti_emojis]


def setup(bot: Ukiyo):
    bot.add_cog(AutoMod(bot))