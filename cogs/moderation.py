from datetime import datetime
from dateutil.relativedelta import relativedelta

import disnake
from disnake.ext import commands, tasks

import utils

from main import Ukiyo


class Moderation(commands.Cog):
    """Staff related commands."""
    def __init__(self, bot: Ukiyo):
        self.bot = bot

        self.check_mutes.start()
        self.check_streaks.start()

    async def check_perms(self, inter: disnake.AppCmdInter) -> bool:
        """
        Returns `False` if the user doesn't have enough perms to use this command
        meaning they're not a staff member, otherwise returns `True` if they're a staff member.
        """

        if not any(r for r in utils.StaffRoles.all if r in (role.id for role in inter.author.roles)):
            if inter.author.id != self.bot._owner_id:
                await inter.send(
                    f'{self.bot.denial} This command can only be used by staff members!',
                    ephemeral=True
            )
                return False
        return True

    @commands.slash_command(name='mute')
    async def mute(
        self,
        inter: disnake.AppCmdInter,
        member: disnake.Member,
        duration: str,
        reason: str
    ):
        """Mutes a member.

        Parameters
        ----------
        member: The member to mute.
        duration: The length for which the mute should last.
        reason: The reason the member is being muted.
        """

        if await self.check_perms(inter) is False:
            return

        try:
            duration = duration.replace(' ', '')  # This is what caused the TypeError
            time_and_reason = await utils.UserFriendlyTime().convert(duration + ' ' + reason)
            mute_duration = utils.human_timedelta(time_and_reason.dt, suffix=False)
            expiration_date = utils.format_dt(time_and_reason.dt, 'F')
        except commands.BadArgument as e:
            return await inter.send(f'{self.bot.denial} {e}', ephemeral=True)
        except TypeError:
            return await inter.send(f'{self.bot.denial} Invalid time provided.', ephemeral=True)

        if member.top_role >= inter.author.top_role and inter.author.id != self.bot._owner_id:
            return await inter.send(
                f'{self.bot.denial} You cannot mute someone that is of higher or equal role to you.',
                ephemeral=True
            )
        elif member.bot:
            return await inter.send(f'{self.bot.denial} Bots can\'t be muted.', ephemeral=True)

        had_entry = True
        entry: utils.Mute = await self.bot.db.get('mutes', member.id)
        if entry is None:
            had_entry = False
            entry: utils.Mute = utils.Mute(
                id=member.id,
                muted_by=inter.author.id
            )
        elif entry.is_muted is True:
            return await inter.send(
                f'{self.bot.denial} That member is already muted!',
                ephemeral=True
            )

        staff_rank = 'Apparently not a staff member, please contact the owner about this issue.'
        _author_roles_ids = [r.id for r in inter.author.roles]
        if utils.StaffRoles.owner in _author_roles_ids or inter.author.id == self.bot._owner_id:
            staff_rank = 'Owner'
        elif utils.StaffRoles.admin in _author_roles_ids:
            staff_rank = 'Admin'
        elif utils.StaffRoles.mod in _author_roles_ids:
            staff_rank = 'Moderator'

        if utils.StaffRoles.owner in (r.id for r in member.roles):  # Checks for owner
            entry.is_owner = True
        elif utils.StaffRoles.admin in (r.id for r in member.roles):  # Checks for admin
            entry.is_admin = True
        elif utils.StaffRoles.mod in (r.id for r in member.roles):  # Checks for mod
            entry.is_mod = True

        guild = self.bot.get_guild(1131710408542146602)
        muted_role = guild.get_role(utils.ExtraRoles.muted)
        new_roles = [r for r in member.roles if r.id not in utils.StaffRoles.all] + [muted_role]
        await member.edit(roles=new_roles, reason=f'Muted by: {inter.author.display_name} ({inter.author.id})')

        em = disnake.Embed()
        em.title = f'You have been muted in `{guild.name}`'
        em.add_field(
            'Reason',
            time_and_reason.arg,
            inline=False
        )
        em.add_field(
            'Duration',
            mute_duration,
            inline=False
        )
        em.add_field(
            'Expires On',
            expiration_date,
            inline=False
        )
        em.add_field(
            'Muted By',
            inter.author.display_name + f' (**{staff_rank}**)',
            inline=False
        )
        em.color = utils.red

        await utils.try_dm(member, embed=em)
        await inter.send(
            f'> 👌 📨 {member.mention} has been muted until {expiration_date} (`{mute_duration}`)'
        )

        entry.muted_until = time_and_reason.dt
        entry.duration = mute_duration
        entry.reason = reason
        entry.is_muted = True

        if had_entry is True:
            await entry.commit()
        else:
            await self.bot.db.add('mutes', entry)

        await utils.log(
            self.bot.webhooks['mod_logs'],
            title=f'[Mute]',
            fields=[
                ('Member', f'{member.display_name} (`{member.id}`)'),
                ('Reason', reason),
                ('Duration', f'`{mute_duration}`'),
                ('Expires At', expiration_date),
                ('By', inter.author.display_name + f' (**{staff_rank}**)'),
                ('At', utils.format_dt(datetime.now(), 'F')),
            ]
        )

    @commands.slash_command(name='unmute')
    async def unmute(self, inter: disnake.AppCmdInter, member: disnake.Member):
        """Unmutes a member.

        Parameters
        ----------
        member: The member you want to unmute.
        """

        if await self.check_perms(inter) is False:
            return

        if member.bot:
            return await inter.send(f'{self.bot.denial} Bots can\'t be muted.', ephemeral=True)

        entry: utils.Mute = await self.bot.db.get('mutes', member.id)
        if entry is None or entry.is_muted is False:
            return await inter.send(f'{self.bot.denial} That member is not muted!', ephemeral=True)

        guild = self.bot.get_guild(1131710408542146602)
        _muted_by = guild.get_member(entry.muted_by)
        new_roles = [r for r in member.roles if r.id != utils.ExtraRoles.muted]
        if entry.is_owner is True:
            new_roles += [guild.get_role(utils.StaffRoles.owner)]
        if entry.is_admin is True:
            new_roles += [guild.get_role(utils.StaffRoles.admin)]
        if entry.is_mod is True:
            new_roles += [guild.get_role(utils.StaffRoles.mod)]

        await member.edit(roles=new_roles, reason=f'Unmuted by: {inter.author.display_name} ({inter.author.id})')

        staff_rank = 'Apparently not a staff member, please contact the owner about this issue.'
        _author_roles_ids = [r.id for r in inter.author.roles]
        if utils.StaffRoles.owner in _author_roles_ids or inter.author.id == self.bot._owner_id:
            staff_rank = 'Owner'
        elif utils.StaffRoles.admin in _author_roles_ids:
            staff_rank = 'Admin'
        elif utils.StaffRoles.mod in _author_roles_ids:
            staff_rank = 'Moderator'

        if entry.filter is True:
            if entry.streak >= 7:
                await self.bot.db.delete('mutes', {'_id': entry.pk})
            else:
                entry.streak_expire_date = datetime.now() + relativedelta(days=21)
                entry.is_muted = False
                await entry.commit()

            muted_by = 'Automod'
        else:
            if entry.streak == 0:
                await self.bot.db.delete('mutes', {'_id': entry.pk})
            else:
                entry.is_muted = False
                await entry.commit()

            muted_by_staff_rank = 'Apparently not a staff member, please contact the owner about this issue.'
            _muted_by_roles_ids = [r.id for r in _muted_by.roles]
            if utils.StaffRoles.owner in _muted_by_roles_ids or _muted_by.id == self.bot._owner_id:
                muted_by_staff_rank = 'Owner'
            elif utils.StaffRoles.admin in _muted_by_roles_ids:
                muted_by_staff_rank = 'Admin'
            elif utils.StaffRoles.mod in _muted_by_roles_ids:
                muted_by_staff_rank = 'Moderator'
            muted_by = f'{_muted_by.display_name} (**{muted_by_staff_rank}**)'

        if entry.permanent is True:
            mute_duration = 'PERMANENT'
            expiration_date = 'PERMANENT'
            remaining = 'PERMANENT'
        else:
            mute_duration = entry.duration
            expiration_date = utils.format_dt(entry.muted_until, 'F')
            remaining = utils.human_timedelta(entry.muted_until, suffix=False)

        em = disnake.Embed()
        em.title = f'You have been unmuted in `{guild.name}`'
        em.add_field(
            'Unmuted By',
            inter.author.display_name + f' (**{staff_rank}**)',
            inline=False
        )
        em.add_field(
            'Original Reason',
            entry.reason,
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
        em.color = utils.green

        await utils.try_dm(member, embed=em)
        await inter.send(
            f'> 👌 {member.mention} has been unmuted.'
        )

        await utils.log(
            self.bot.webhooks['mod_logs'],
            title=f'[UNMUTE]',
            fields=[
                ('Member', f'{member.display_name} (`{member.id}`)'),
                ('Original Reason', entry.reason),
                ('Original Duration', f'`{mute_duration}`'),
                ('Original Expiration Date', expiration_date),
                ('Remaining', f'`{remaining}`'),
                ('Originally Muted By', muted_by),
                ('By', f'{inter.author.mention} (`{inter.author.id}`)'),
                ('At', utils.format_dt(datetime.now(), 'F')),
            ]
        )

    @tasks.loop(seconds=5.0)
    async def check_mutes(self):
        entries: list[utils.Mute] = await self.bot.db.find_sorted('mutes', 'muted_until', 1, {'is_muted': True})
        for entry in entries[:15]:
            if datetime.now(entry.muted_until.tzinfo) >= entry.muted_until:
                guild = self.bot.get_guild(1131710408542146602)
                member = guild.get_member(entry.id)
                _mem = f'**[LEFT]** (`{entry.id}`)'

                if member:
                    _mem = f'{member.display_name} (`{member.id}`)'
                    new_roles = [role for role in member.roles if role.id != utils.ExtraRoles.muted]
                    if entry.is_owner is True:
                        owner_role = guild.get_role(utils.StaffRoles.owner)  # Check for owner
                        new_roles += [owner_role]
                    elif entry.is_admin is True:
                        admin_role = guild.get_role(utils.StaffRoles.admin)  # Check for admin
                        new_roles += [admin_role]
                    elif entry.is_mod is True:
                        mod_role = guild.get_role(utils.StaffRoles.mod)  # Check for mod
                        new_roles += [mod_role]
                    await member.edit(roles=new_roles, reason=f'[UNMUTE] Mute Expired.')
                    await utils.try_dm(
                        member,
                        f'Hello, your mute in `{guild.name}` has expired. You have been unmuted.'
                    )

                if entry.filter is True:
                    if entry.streak >= 7:
                        await self.bot.db.delete('mutes', {'_id': entry.pk})
                    else:
                        entry.is_muted = False
                        entry.streak_expire_date = datetime.now() + relativedelta(days=21)
                        await entry.commit()
                else:
                    if entry.streak == 0:
                        await self.bot.db.delete('mutes', {'_id': entry.id})
                    else:
                        entry.is_muted = False
                        await entry.commit()

                mem = guild.get_member(entry.muted_by)
                await utils.log(
                    self.bot.webhooks['mod_logs'],
                    title='[MUTE EXPIRED]',
                    fields=[
                        ('Member', _mem),
                        ('Reason', entry.reason),
                        ('Mute Duration', f'`{entry.duration}`'),
                        ('By', mem.mention),
                        ('At', utils.format_dt(datetime.now(), 'F')),
                    ]
                )

    @check_mutes.before_loop
    async def mutes_wait_until_ready(self):
        await self.bot.wait_until_ready()

    @tasks.loop(seconds=5.0)
    async def check_streaks(self):
        entries: list[utils.Mute] = await self.bot.db.find_sorted('mutes', 'streak_expire_date', 1, {'is_muted': False})
        for entry in entries[:10]:
            if datetime.now() >= entry.streak_expire_date:
                await self.bot.db.delete('mutes', {'_id': entry.pk})

                guild = self.bot.get_guild(1131710408542146602)
                usr = guild.get_member(entry.id)
                if usr:
                    mem = f'{usr.display_name} (`{usr.id}`)'
                else:
                    mem = f'**[LEFT]** (`{entry.id}`)'

                await utils.log(
                    self.bot.webhooks['mod_logs'],
                    title='[STREAK RESET]',
                    fields=[
                        ('User', mem),
                        ('At', utils.format_dt(datetime.now(), 'F')),
                    ]
                )

    @check_streaks.before_loop
    async def streaks_wait_until_ready(self):
        await self.bot.wait_until_ready()

    @commands.slash_command(name='ban')
    async def ban(self, inter: disnake.AppCmdInter, member: disnake.Member, reason: str):
        """Ban a member.

        Parameters
        ----------
        member: The member you want to ban.
        reason: The reason you're banning them.
        """

        if await self.check_perms(inter) is False:
            return

        if not any(r for r in (utils.StaffRoles.owner, utils.StaffRoles.admin) if r in (role.id for role in inter.author.roles)):
            if inter.author.id != self.bot._owner_id:
                await inter.send(
                    f'{self.bot.denial} This command can only be used by admins and above!',
                    ephemeral=True
                )

        if member.top_role >= inter.author.top_role and inter.author.id != self.bot._owner_id:
            return await inter.send(
                f'{self.bot.denial} You cannot ban someone that is of higher or equal role to you.',
                ephemeral=True
            )

        staff_rank = 'Apparently not a staff member, please contact the owner about this issue.'
        _author_roles_ids = [r.id for r in inter.author.roles]
        if utils.StaffRoles.owner in _author_roles_ids or inter.author.id == self.bot._owner_id:
            staff_rank = 'Owner'
        elif utils.StaffRoles.admin in _author_roles_ids:
            staff_rank = 'Admin'

        em = disnake.Embed()
        em.title = f'You have been banned in `{inter.guild.name}`'
        em.add_field(
            'Banned By',
            inter.author.display_name + f' (**{staff_rank}**)',
            inline=False
        )
        em.add_field(
            'Reason',
            reason,
            inline=False
        )

        await utils.try_dm(member, embed=em)
        await member.ban(
            clean_history_duration=0,
            reason=f'{inter.author.display_name}: {reason}'
        )
        await inter.send(
            f'> 👌 {member.mention} has been banned.'
        )

        await utils.log(
            self.bot.webhooks['mod_logs'],
            title=f'[BAN]',
            fields=[
                ('Member', f'{member.display_name} (`{member.id}`)'),
                ('Reason', reason),
                ('By', f'{inter.author.mention} (`{inter.author.id}`)'),
                ('At', utils.format_dt(datetime.now(), 'F')),
            ]
        )

    @commands.slash_command(name='kick')
    async def kick(self, inter: disnake.AppCmdInter, member: disnake.Member, reason: str):
        """Kick a member.

        Parameters
        ----------
        member: The member you want to kick.
        reason: The reason you're kicking them.
        """

        if await self.check_perms(inter) is False:
            return

        if member.top_role >= inter.author.top_role and inter.author.id != self.bot._owner_id:
            return await inter.send(
                f'{self.bot.denial} You cannot kick someone that is of higher or equal role to you.',
                ephemeral=True
            )

        staff_rank = 'Apparently not a staff member, please contact the owner about this issue.'
        _author_roles_ids = [r.id for r in inter.author.roles]
        if utils.StaffRoles.owner in _author_roles_ids or inter.author.id == self.bot._owner_id:
            staff_rank = 'Owner'
        elif utils.StaffRoles.admin in _author_roles_ids:
            staff_rank = 'Admin'
        elif utils.StaffRoles.mod in _author_roles_ids:
            staff_rank = 'Moderator'

        em = disnake.Embed()
        em.title = f'You have been kicked in `{inter.guild.name}`'
        em.add_field(
            'Kicked By',
            inter.author.display_name + f' (**{staff_rank}**)',
            inline=False
        )
        em.add_field(
            'Reason',
            reason,
            inline=False
        )

        await utils.try_dm(member, embed=em)
        await member.kick(reason=f'{inter.author.display_name}: {reason}')
        await inter.send(
            f'> 👌 {member.mention} has been kicked.'
        )

        await utils.log(
            self.bot.webhooks['mod_logs'],
            title=f'[KICK]',
            fields=[
                ('Member', f'{member.display_name} (`{member.id}`)'),
                ('Reason', reason),
                ('By', f'{inter.author.mention} (`{inter.author.id}`)'),
                ('At', utils.format_dt(datetime.now(), 'F')),
            ]
        )

    @commands.slash_command(name='purge')
    async def purge(self, inter: disnake.AppCmdInter, amount: int = commands.Param(ge=1)):
        """Purge an amount of messages from the current channel.

        Parameters
        ----------
        amount: The amount of messages to delete.
        """

        if await self.check_perms(inter) is False:
            return

        await inter.response.defer()

        messages = await inter.channel.purge(limit=amount)
        await inter.channel.send(f'> 👌 Purged `{len(messages):,}` messages.', delete_after=5.0)

        await utils.log(
            self.bot.webhooks['mod_logs'],
            title='[CHAT PURGE]',
            fields=[
                ('Channel', inter.channel.mention),
                ('Amount', f'`{utils.plural(len(messages)):message}`'),
                ('By', f'{inter.author.mention} (`{inter.author.id}`)'),
                ('At', utils.format_dt(datetime.now(), 'F')),
            ]
        )

    @commands.slash_command(name='lockdown')
    async def lockdown(self, inter: disnake.AppCmdInter):
        """Locks down all channels."""

        if await self.check_perms(inter) is False:
            return

        await inter.response.defer()  # We defer since this may take a while.

        entry: utils.Misc = await self.bot.db.get('misc')
        entry.in_lockdown = not entry.in_lockdown
        await entry.commit()

        value = None if entry.in_lockdown is False else False

        guild = self.bot.get_guild(1131710408542146602)
        for text_channel in guild.text_channels:
            if text_channel.id not in (
                utils.Channels.verify, utils.Channels.rules, utils.Channels.welcome,
                utils.Channels.intros, utils.Channels.how_to, utils.Channels.staff_chat,
                utils.Channels.bot_commands, utils.Channels.ideas, utils.Channels.lore_shit,
                utils.Channels.logs, utils.Channels.messages_logs, utils.Channels.moderation_logs,
                utils.Channels.github, utils.Channels.discord_notifications, utils.Channels.roblox_logs,
                utils.Channels.news
            ):
                overwrite = text_channel.overwrites_for(guild.default_role)
                overwrite.send_messages = value
                await text_channel.set_permissions(guild.default_role, overwrite=overwrite)

        for voice_channel in guild.voice_channels:
            overwrite = voice_channel.overwrites_for(guild.default_role)
            overwrite.speak = value
            await voice_channel.set_permissions(guild.default_role, overwrite=overwrite)

        if value is None:
            return await inter.send('> 👌 Lockdown ended.')
        await inter.send('> 👌 All channels have been locked down.')

    @commands.slash_command(name='badwords')
    async def bad_words(self, inter):
        pass

    @bad_words.sub_command(name='view')
    async def bad_words_view(self, inter: disnake.AppCmdInter):
        """See a list of all the currently added bad words."""

        if await self.check_perms(inter) is False:
            return

        entry: utils.Misc = await self.bot.db.get('misc')
        if len(entry.bad_words) == 0:
            return await inter.send(
                f'{self.bot.denial} There are no currently added bad words.',
                ephemeral=True
            )

        guild = self.bot.get_guild(1131710408542146602)
        sorted_ = [w for w in sorted(entry.bad_words.keys())]
        entries = []
        for word in sorted_:
            added_by_id = entry.bad_words[word]
            added_by = guild.get_member(added_by_id)
            added_by = f'**{added_by.display_name}**' or '**[LEFT]**'
            added_by = added_by + f' (`{added_by_id}`)'

            entries.append(
                f'`{word}` - added by {added_by}'
            )

        pag = utils.SimplePages(inter, entries, compact=True, entries_name='bad words')
        pag.embed.title = 'Here\'s all the currently added bad words'
        await pag.start()

    @bad_words.sub_command(name='add')
    async def bad_words_add(self, inter: disnake.AppCmdInter, word: str):
        """Adds a bad word to the existing bad words.

        Parameters
        ----------
        word: The bad word you want to add.
        """

        if await self.check_perms(inter) is False:
            return

        if not any(r for r in (utils.StaffRoles.owner, utils.StaffRoles.admin) if r in (role.id for role in inter.author.roles)):
            if inter.author.id != self.bot._owner_id:
                await inter.send(
                    f'{self.bot.denial} This command can only be used by admins and above!',
                    ephemeral=True
                )

        word = word.lower()
        entry: utils.Misc = await self.bot.db.get('misc')

        if word in [w for w in entry.bad_words.keys()]:
            return await inter.send(
                f'{self.bot.denial} That bad word is already added in the list.',
                ephemeral=True
            )

        self.bot.bad_words[word] = inter.author.id
        entry.bad_words[word] = inter.author.id
        await entry.commit()

        await inter.send(f'Successfully **added** `{word}` to the bad words list.')

    @bad_words.sub_command(name='remove')
    async def bad_words_remove(self, inter: disnake.AppCmdInter, word: str):
        """Removes a bad word to the existing bad words.

        Parameters
        ----------
        word: The word you want to remove.
        """

        if await self.check_perms(inter) is False:
            return

        if not any(r for r in (utils.StaffRoles.owner, utils.StaffRoles.admin) if r in (role.id for role in inter.author.roles)):
            if inter.author.id != self.bot._owner_id:
                await inter.send(
                    f'{self.bot.denial} This command can only be used by admins and above!',
                    ephemeral=True
                )

        word = word.lower()
        entry: utils.Misc = await self.bot.db.get('misc')
        if len(entry.bad_words) == 0:
            return await inter.send(
                f'{self.bot.denial} There are no currently added bad words.',
                ephemeral=True
            )
        elif word not in entry.bad_words.keys():
            return await inter.send(
                f'{self.bot.denial} That word is not added in list of bad words.',
                ephemeral=True
            )

        del entry.bad_words[word]
        del self.bot.bad_words[word]
        await entry.commit()

        await inter.send(f'Successfully **removed** `{word}` to the bad words list.')

    @bad_words.sub_command(name='clear')
    async def clear_bad_word(self, inter: disnake.AppCmdInter):
        """Clear the custom bad words. This deletes all of them."""

        if await self.check_perms(inter) is False:
            return

        if not any(r for r in (utils.StaffRoles.owner,) if r in (role.id for role in inter.author.roles)):
            if inter.author.id != self.bot._owner_id:
                await inter.send(
                    f'{self.bot.denial} This command can only be used by owners!',
                    ephemeral=True
                )

        entry: utils.Misc = await self.bot.db.get('misc')
        if len(entry.bad_words) == 0:
            return await inter.send(
                f'{self.bot.denial} There are no currently added bad words.',
                ephemeral=True
            )

        entry.bad_words = {}
        self.bot.bad_words = {}
        await entry.commit()

        await inter.send('Successfully **cleared** the bad words list.')


def setup(bot: Ukiyo):
    bot.add_cog(Moderation(bot))
