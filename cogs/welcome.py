import os

from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

import disnake
from disnake.ext import commands, tasks

import utils

from main import Ukiyo


class Welcome(commands.Cog):
    def __init__(self, bot: Ukiyo):
        self.bot = bot
        self.files = {}
        self.send_welc.start()

    @tasks.loop(seconds=15.0)
    async def send_welc(self):
        if self.files:
            webhook = self.bot.webhooks.get('welcome_webhook')
            if webhook is not None:
                if len(self.files) == 10:
                    await webhook.send(files=self.files.values())
                else:
                    files = []
                    count = 0
                    for file in self.files.values():
                        count += 1
                        files.append(file)
                        if count == 10:
                            await webhook.send(files=files)
                            count = 0
                            files = []
                    if len(files) != 0:
                        await webhook.send(files=files)
                        files = []
                self.files = {}

                # We delete all the png files in the folder
                # so that they don't stack up a lot and end up
                # using a ton of space when they're useless to be
                # kept.
                os.system('rm welcomes/*')

    @commands.Cog.listener('on_member_join')
    async def on_member_join(self, member: disnake.Member):
        entry: utils.Misc = await self.bot.db.get('misc')
        days_ago = datetime.now(timezone.utc) - relativedelta(days=entry.min_account_age)
        if member.created_at > days_ago:
            await utils.try_dm(member, 'Your account is too new to be allowed in the server.')
            await member.ban(reason='Account too new.')
            return await utils.log(
                self.bot.webhooks['mod_logs'],
                title='[BAN]',
                fields=[
                    ('Member', f'{member.display_name} (`{member.id}`)'),
                    ('Reason', 'Account too new.'),
                    ('Account Created', utils.human_timedelta(member.created_at, accuracy=7)),
                    ('By', f'{self.bot.user.mention} (`{self.bot.user.id}`)'),
                    ('At', utils.format_dt(datetime.now(), 'F')),
                ]
            )

        if member.guild.id != 1131710408542146602:  # Only continue if it's actual ukiyo server.
            return

        guild = self.bot.get_guild(1131710408542146602)
        if member.bot:
            bot_role = guild.get_role(utils.ExtraRoles.bot)
            await member.add_roles(bot_role, reason='Bot Account.')
            return

        await utils.check_username(self.bot, member=member, bad_words=self.bot.bad_words.keys())
        unverified_role = guild.get_role(utils.ExtraRoles.unverified)
        await member.add_roles(unverified_role)

        member_count = len([m for m in guild.members if not m.bot])
        file = await utils.create_welcome_card(member, member_count)
        self.files[member.id] = file

        mute: utils.Mute = await self.bot.db.get('mute', member.id)
        if mute is not None and mute.is_muted is True:
            if mute.permanent is True:
                mute_duration = 'PERMANENT'
                expiration_date = 'PERMANENT'
                remaining = 'PERMANENT'
            else:
                mute_duration = mute.duration
                expiration_date = utils.format_dt(mute.muted_until, 'F')
                remaining = utils.human_timedelta(mute.muted_until, suffix=False)

            role = guild.get_role(utils.ExtraRoles.muted)
            _muted_by = guild.get_member(mute.muted_by)
            await member.add_roles(role, reason=f'[MUTE EVASION] user joined but was still muted.')

            if mute.filter is True:
                muted_by = 'Automod'
            else:
                muted_by_staff_rank = 'Apparently not a staff member, please contact the owner about this issue.'
                _muted_by_roles_ids = [r.id for r in _muted_by.roles]
                if utils.StaffRoles.owner in _muted_by_roles_ids or _muted_by.id == self.bot._owner_id:
                    muted_by_staff_rank = 'Owner'
                elif utils.StaffRoles.admin in _muted_by_roles_ids:
                    muted_by_staff_rank = 'Admin'
                elif utils.StaffRoles.mod in _muted_by_roles_ids:
                    muted_by_staff_rank = 'Moderator'
                muted_by = f'{_muted_by.display_name} (**{muted_by_staff_rank}**)'

            em = disnake.Embed()
            em.title = f'You have been muted in `{guild.name}`'
            em.add_field(
                'Muted By',
                'Automod',
                inline=False
            )
            em.add_field(
                'Reason',
                'Mute Evasion',
                inline=False
            )
            em.add_field(
                'Original Reason',
                mute.reason,
                inline=False
            )
            em.add_field(
                'Original Duration',
                mute_duration,
                inline=False
            )
            em.add_field(
                'Original Expiration date',
                expiration_date,
                inline=False
            )
            em.add_field(
                'Time Remaining',
                remaining,
                inline=False
            )
            em.add_field(
                'Originally Muted By',
                muted_by,
                inline=False
            )
            em.color = utils.red

            await utils.try_dm(member, embed=em)

            await utils.log(
                self.bot.webhooks['mod_logs'],
                title=f'[MUTE]',
                fields=[
                    ('Member', f'{member.display_name} (`{member.id}`)'),
                    ('Reason', 'Mute Evasion'),
                    ('Original Reason', mute.reason),
                    ('Original Duration', f'`{mute_duration}`'),
                    ('Original Expiration Date', expiration_date),
                    ('Remaining', f'`{remaining}`'),
                    ('Originally Muted By', muted_by),
                    ('By', 'Automod'),
                    ('At', utils.format_dt(datetime.now(), 'F')),
                ]
            )

    @commands.Cog.listener()
    async def on_member_remove(self, member: disnake.Member):
        if member.guild.id != 1131710408542146602:
            return

        if member.id in self.files:
            del self.files[member.id]


def setup(bot: Ukiyo):
    bot.add_cog(Welcome(bot))
