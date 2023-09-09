from typing import Sequence
import datetime

import disnake
from disnake.ext import commands, tasks

import utils

from main import Ukiyo


class Logs(commands.Cog):
    def __init__(self, bot: Ukiyo):
        self.bot = bot
        self.send_embeds.start()
        self.embeds = []

    @tasks.loop(minutes=1.0)
    async def send_embeds(self):
        if len(self.embeds) != 0:
            try:
                await utils.send_embeds(self.bot.webhooks['logs'], self.embeds)
            except Exception:
                pass
            self.embeds = []

    @send_embeds.before_loop
    async def wait_until_ready(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_user_update(self, before: disnake.User, after: disnake.User):
        em = disnake.Embed(
            description=f'**{after.mention} updated their profile:**',
            timestamp=datetime.datetime.utcnow(),
            color=disnake.Color.yellow()
        )
        em.set_author(name=before.display_name, icon_url=before.display_avatar)
        em.set_thumbnail(url=after.display_avatar)
        em.set_footer(text=f'User ID: {after.id}')

        if before.name != after.name:
            em.add_field(name='Username', value=f'`{before.name}` **->** `{after.name}`', inline=False)

        if before.discriminator != after.discriminator:
            em.add_field(name='Discriminator', value=f'`#{before.discriminator}` **->** `#{after.discriminator}`', inline=False)

        if before.display_avatar != after.display_avatar:
            em.add_field(name='Avatar', value=f'[`Before`]({before.display_avatar}) -> [`After`]({after.display_avatar})', inline=False)

        if len(em.fields) != 0:
            self.embeds.append(em)

    @commands.Cog.listener()
    async def on_member_update(self, before: disnake.Member, after: disnake.Member):
        if before.guild.id != 1131710408542146602:
            return

        em = disnake.Embed(timestamp=datetime.datetime.utcnow(), color=disnake.Color.yellow())
        em.set_author(name=before.display_name, icon_url=before.display_avatar)
        em.set_thumbnail(url=after.display_avatar)
        em.set_footer(text=f'Member ID: {after.id}')

        if before.nick != after.nick:
            em.add_field(name='Nickname', value=f'`{before.nick}` **->** `{after.nick}`', inline=False)

        if before.roles != after.roles:
            removed_roles = []
            added_roles = []
            for role in before.roles:
                if role not in after.roles:
                    removed_roles.append(role)
            for role in after.roles:
                if role not in before.roles:
                    added_roles.append(role)
            if len(added_roles) != 0:
                em.add_field(name=r'\✅ Added Roles', value=', '.join([role.name for role in added_roles]), inline=False)
            if len(removed_roles) != 0:
                em.add_field(name=r'\❌ Removed Roles', value=', '.join([role.name for role in removed_roles]), inline=False)

        if len(em.fields) != 0:
            self.embeds.append(em)

    @commands.Cog.listener()
    async def on_member_join(self, member: disnake.Member):
        if member.guild.id != 1131710408542146602:
            return

        em = disnake.Embed(description=f'📥 **{member.mention} joined the server**', timestamp=datetime.datetime.utcnow(), color=disnake.Color.green())
        em.set_author(name=member.name, icon_url=member.display_avatar)
        em.set_thumbnail(url=member.display_avatar)
        em.set_footer(text=f'Member ID: {member.id}')
        em.add_field(name='Account Creation', value=utils.human_timedelta(member.created_at))

        self.embeds.append(em)

    @commands.Cog.listener()
    async def on_member_remove(self, member: disnake.Member):
        if member.guild.id != 1131710408542146602:
            return

        em = disnake.Embed(description=f'📤 **{member.mention} left the server**', timestamp=datetime.datetime.utcnow(), color=disnake.Color.red())
        em.set_author(name=member.display_name, icon_url=member.display_avatar)
        em.set_thumbnail(url=member.display_avatar)
        em.set_footer(text=f'User ID: {member.id}')

        self.embeds.append(em)

    @commands.Cog.listener()
    async def on_member_ban(self, guild: disnake.Guild, member: disnake.Member | disnake.User):
        if guild.id != 1131710408542146602:
            return

        em = disnake.Embed(description=f'👮‍♂️🔒 **{member.mention} was banned**', timestamp=datetime.datetime.utcnow(), color=disnake.Color.red())
        em.set_author(name=member.display_name, icon_url=member.display_avatar)
        em.set_thumbnail(url=member.display_avatar)
        em.set_footer(text=f'User ID: {member.id}')

        self.embeds.append(em)

    @commands.Cog.listener()
    async def on_member_unban(self, guild: disnake.Guild, user: disnake.User):
        if guild.id != 1131710408542146602:
            return

        em = disnake.Embed(description=f'👮‍♂️🔓 **{user.mention} was unbanned**', timestamp=datetime.datetime.utcnow(), color=disnake.Color.green())
        em.set_author(name=user.name, icon_url=user.display_avatar)
        em.set_thumbnail(url=user.display_avatar)
        em.set_footer(text=f'User ID: {user.id}')

        self.embeds.append(em)

    @commands.Cog.listener()
    async def on_guild_update(self, before: disnake.Guild, after: disnake.Guild):
        if before.id != 1131710408542146602:
            return

        em = disnake.Embed(color=disnake.Color.yellow(), timestamp=datetime.datetime.utcnow())
        em.set_thumbnail(url=before.icon)
        em.title = 'Guild Updated'

        if before.name != after.name:
            em.add_field(name='Name', value=f'`{before.name}` **->** `{after.name}`', inline=False)
            em.set_thumbnail(url=after.icon.url)

        if before.description != after.description:
            em.add_field(name='Description', value=f'`{before.description}` **->** `{after.description}`', inline=False)

        if before.icon != after.icon:
            if before.icon is not None:
                before_icon = f'[`Before`]({before.icon.url})'
            else:
                before_icon = '`None`'
            if after.icon is not None:
                after_icon = f'[`After`]({after.icon.url})'
            else:
                after_icon = '`None`'
            em.add_field(name='Icon', value=f'{before_icon} **->** {after_icon}', inline=False)

        if before.banner != after.banner:
            if before.banner is not None:
                before_banner = f'[`Before`]({before.banner.url})'
            else:
                before_banner = '`None`'
            if after.banner is not None:
                after_banner = f'[`After`]({after.banner.url})'
            else:
                after_banner = '`None`'
            em.add_field(name='Banner', value=f'{before_banner} **->** {after_banner}', inline=False)

        if before.splash != after.splash:
            if before.splash is not None:
                before_splash = f'[`Before`]({before.splash.url})'
            else:
                before_splash = '`None`'
            if after.splash is not None:
                after_splash = f'[`After`]({after.splash.url})'
            else:
                after_splash = '`None`'
            em.add_field(name='Invite Background', value=f'{before_splash} **->** {after_splash}', inline=False)

        if before.afk_channel != after.afk_channel:
            em.add_field(name='AFK Channel', value=f'`{before.afk_channel}` **->** `{after.afk_channel}`', inline=False)

        if before.afk_timeout != after.afk_timeout:
            before_timeout = '0 seconds' if before.afk_timeout == 0 else utils.time_phaser(before.afk_timeout)
            after_timeout = '0 seconds' if after.afk_timeout == 0 else utils.time_phaser(after.afk_timeout)
            em.add_field(
                name='AFK Timeout',
                value=f'`{before_timeout}` **->** `{after_timeout}`',
                inline=False
            )

        if before.default_notifications != after.default_notifications:
            _ = {
                0: '`All Messages`',
                1: '`Mentions Only`'
            }
            em.add_field(
                name='Default Notifications',
                value=f'{_[before.default_notifications.value]} **->** {_[after.default_notifications.value]}',
                inline=False
            )

        if before.emoji_limit != after.emoji_limit:
            em.add_field(name='Emojis Limit', value=f'`{before.emoji_limit}` **->** `{after.emoji_limit}`', inline=False)

        if before.sticker_limit != after.sticker_limit:
            em.add_field(name='Stickers Limit', value=f'`{before.sticker_limit}` **->** `{after.sticker_limit}`', inline=False)

        if before.verification_level != after.verification_level:
            em.add_field(
                name='Verification Level',
                value=f'`{str(before.verification_level).title()}` **->** `{str(after.verification_level).title()}`',
                inline=False
            )

        if before.mfa_level != after.mfa_level:
            _ = {
                0: 'False',
                1: 'True'
            }
            em.add_field(
                name='2 Factor Authentication',
                value=f'`{_[str(before.mfa_level)]}` **->** `{str(after.mfa_level)}`',
                inline=False
            )

        if before.explicit_content_filter != after.explicit_content_filter:
            before_filter = str(before.explicit_content_filter).replace('_', ' ').title()
            after_filter = str(after.explicit_content_filter).replace('_', ' ').title()
            em.add_field(
                name='Explicit Content Filter',
                value=f'`{before_filter}` **->** `{after_filter}`',
                inline=False
            )

        if before.system_channel != after.system_channel:
            em.add_field(
                name='System Channel',
                value=f'`{before.system_channel}` **->** `{after.system_channel}`',
                inline=False
            )

        if before.rules_channel != after.rules_channel:
            em.add_field(name='Rules Channel', value=f'`{before.rules_channel}` **->** `{after.rules_channel}`', inline=False)

        if before.public_updates_channel != after.public_updates_channel:
            em.add_field(
                name='Public Updates Channel',
                value=f'`{before.public_updates_channel}` **->** `{after.public_updates_channel}`',
                inline=False
            )

        if before.premium_progress_bar_enabled != after.premium_progress_bar_enabled:
            em.add_field(
                name='Premium Progress Bar Visibility',
                value=f'`{before.premium_progress_bar_enabled}` **->** `{after.premium_progress_bar_enabled}`',
                inline=False
            )

        if before.premium_tier != after.premium_tier:
            em.add_field(
                name='Boosts Level',
                value=f'`{before.premium_tier}` **->** {after.premium_tier}',
                inline=False
            )

        if len(em.fields) != 0:
            self.embeds.append(em)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: disnake.Role):
        if role.guild.id != 1131710408542146602:
            return

        em = disnake.Embed(title=f'Role Created: {role.name}', color=disnake.Color.green(), timestamp=datetime.datetime.utcnow())
        em.add_field(name='Permissions', value=', '.join((perm[0].replace('_', ' ') for perm in (p for p in role.permissions) if perm[1] is True)))

        self.embeds.append(em)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: disnake.Role):
        if role.guild.id != 1131710408542146602:
            return

        em = disnake.Embed(title=f'Role Deleted: {role.name}', color=disnake.Color.red(), timestamp=datetime.datetime.utcnow())
        em.add_field(name='Colour', value=f'[`{role.colour}`](https://www.color-hex.com/color/{str(role.colour).replace("#", "")})')
        em.add_field(name='Hoisted', value='No' if role.hoist is False else 'Yes')
        em.add_field(name='Mentionable', value='No' if role.mentionable is False else True)
        em.add_field(name='Permissions', value=', '.join((perm[0].replace('_', ' ') for perm in (p for p in role.permissions) if perm[1] is True)))
        em.set_footer(text=f'Role ID: {role.id}')

        self.embeds.append(em)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: disnake.Role, after: disnake.Role):
        if before.guild.id != 1131710408542146602:
            return

        em = disnake.Embed(
            title=f'Role Updated: {after.name}',
            description=f'`{before.name}` has been updated',
            color=disnake.Color.yellow(),
            timestamp=datetime.datetime.utcnow()
        )
        em.set_footer(text=f'Role ID: {after.id}')
        em.set_thumbnail(url=before.guild.icon.url)

        if before.name != after.name:
            em.add_field(name='Name', value=f'`{before.name}` **->** `{after.name}`', inline=False)

        if before.color != after.color:
            em.add_field(name='Colour', value=f'`{before.colour}` **->** `{after.colour}`', inline=False)

        if before.hoist != after.hoist:
            em.add_field(name='Hoisted', value=f'`{before.hoist}` **->** `{after.hoist}`', inline=False)

        if before.mentionable != after.mentionable:
            em.add_field(name='Mentionable', value=f'`{before.mentionable}` **->** `{after.mentionable}`', inline=False)

        if before.permissions != after.permissions:
            added_perms = []
            removed_perms = []

            old_perms = {}
            for perm in before.permissions:
                old_perms[perm[0]] = perm[1]

            for perm in after.permissions:
                if perm[1] != old_perms[perm[0]]:
                    if perm[1] is False:
                        removed_perms.append(perm[0].replace('_', ' ').title())
                    elif perm[1] is True:
                        added_perms.append(perm[0].replace('_', ' ').title())

            if len(added_perms) != 0:
                em.add_field(name=r'\✅ Added Permissions', value=f'`{"`, `".join(added_perms)}`', inline=False)
            if len(removed_perms) != 0:
                em.add_field(name=r'\❌ Removed Permissions', value=f'`{"`, `".join(removed_perms)}`', inline=False)

        if len(em.fields) != 0:
            self.embeds.append(em)

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild: disnake.Guild, before: Sequence[disnake.Emoji], after: Sequence[disnake.Emoji]):
        if guild.id != 1131710408542146602:
            return

        em = disnake.Embed(title='Emoji Updated', color=disnake.Color.yellow(), timestamp=datetime.datetime.utcnow())
        added_emoji = None
        removed_emoji = None
        old_name = None
        new_name = None

        for emoji in before:
            if emoji.id in (e.id for e in after):
                if emoji.name != ''.join([e.name for e in after if e.id == emoji.id]):
                    old_name = emoji.name
                    new_name = ''.join([e.name for e in after if e.id == emoji.id])
                    break
        for emoji in before:
            if emoji.id not in (e.id for e in after):
                removed_emoji = (emoji.name, emoji.url)
                break
        for emoji in after:
            if emoji.id not in (e.id for e in before):
                added_emoji = emoji
                break

        if new_name is not None:
            em.add_field(name='Emoji Name Changed', value=f'`{old_name}` **->** `{new_name}`', inline=False)

        if added_emoji is not None:
            em.add_field(name=r'\✅ Added Emoji', value='`' + str(added_emoji) + '`', inline=False)
            em.set_thumbnail(url=emoji.url)

        if removed_emoji is not None:
            em.add_field(name=r'\❌ Removed Emoji', value=f'[`{removed_emoji[0]}`]({removed_emoji[1]})', inline=False)
            em.set_thumbnail(url=removed_emoji[1])

        if len(em.fields) != 0:
            self.embeds.append(em)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: disnake.abc.GuildChannel):
        if channel.guild.id != 1131710408542146602:
            return

        em = disnake.Embed(title='Channel Created', color=disnake.Color.green(), timestamp=datetime.datetime.utcnow())
        em.set_footer(text=f'Channel ID: {channel.id}')
        em.add_field(name='Name', value=f'`{channel.name}`', inline=False)
        em.add_field(name='Type', value=f'`{str(channel.type).title()} Channel`', inline=False)

        self.embeds.append(em)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: disnake.abc.GuildChannel):
        if channel.guild.id != 1131710408542146602:
            return

        em = disnake.Embed(title='Channel Deleted', color=disnake.Color.red(), timestamp=datetime.datetime.utcnow())
        em.add_field(name='Name', value=f'`{channel.name}`', inline=False)
        em.add_field(name='Type', value=f'`{str(channel.type).title()} Channel`', inline=False)

        self.embeds.append(em)

    @commands.Cog.listener('on_guild_channel_update')
    async def mem_perm_add(self, before: disnake.abc.GuildChannel, after: disnake.abc.GuildChannel):
        if before.guild.id != 1131710408542146602:
            return

        em = disnake.Embed(title=f'Channel Updated: {before.name}', color=disnake.Color.yellow(), timestamp=datetime.datetime.utcnow())
        em.set_footer(text=f'Channel ID: {after.id}')

        if before.overwrites != after.overwrites:
            added_overwrites = []
            removed_overwrites = []

            for overwrite in after.overwrites:
                if overwrite not in before.overwrites:
                    added_overwrites.append(f'`{overwrite.name}`')
            for overwrite in before.overwrites:
                if overwrite not in after.overwrites:
                    removed_overwrites.append(f'`{overwrite.name}`')

            if len(added_overwrites) != 0:
                em.description = f'Added permissions for {", ".join(added_overwrites)}'
                em.color = disnake.Colour.green()
                self.embeds.append(em)
            if len(removed_overwrites) != 0:
                em.description = f'Removed permissions for {", ".join(removed_overwrites)}'
                em.color = disnake.Colour.red()
                self.embeds.append(em)

    @commands.Cog.listener('on_guild_channel_update')
    async def overwrites_update(self, before: disnake.abc.GuildChannel, after: disnake.abc.GuildChannel):
        if before.guild.id != 1131710408542146602:
            return

        em = disnake.Embed(title=f'Channel Updated: {before.name}', color=disnake.Color.yellow(), timestamp=datetime.datetime.utcnow())
        em.set_footer(text=f'Channel ID: {after.id}')
        if before.overwrites != after.overwrites:
            allowed_perms = []
            neutral_perms = []
            denied_perms = []
            old_perms = {}

            for k in before.overwrites:
                perms = {}
                for v in before.overwrites[k]:
                    perms[v[0]] = v[1]
                old_perms[k.id] = perms

            for k in after.overwrites:
                for v in after.overwrites[k]:
                    try:
                        if v[1] != old_perms[k.id][v[0]]:
                            em.description = f'Edited permissions for `{k}`'
                            if v[1] is False:
                                denied_perms.append(v[0])
                            elif v[1] is None:
                                neutral_perms.append(v[0])
                            elif v[1] is True:
                                allowed_perms.append(v[0])
                    except KeyError:
                        pass

            if len(allowed_perms) != 0:
                em.add_field(name=r'\✅ Allowed Perms', value=', '.join(allowed_perms), inline=False)
            if len(neutral_perms) != 0:
                em.add_field(name='⧄ Neutral Perms', value=', '.join(neutral_perms), inline=False)
            if len(denied_perms) != 0:
                em.add_field(name=r'\❌ Denied Perms', value=', '.join(denied_perms), inline=False)

        if len(em.fields) != 0:
            self.embeds.append(em)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: disnake.abc.GuildChannel, after: disnake.abc.GuildChannel):
        if before.guild.id != 1131710408542146602:
            return

        em = disnake.Embed(title=f'Channel Updated: {before.name}', color=disnake.Color.yellow(), timestamp=datetime.datetime.utcnow())
        em.set_footer(text=f'Channel ID: {after.id}')

        if before.name != after.name:
            em.add_field(name='Name', value=f'`{before.name}` **->** `{after.name}`', inline=False)

        try:
            if before.topic != after.topic:
                em.add_field(name='Topic', value=f'`{before.topic}` **->** `{after.topic}`', inline=False)
        except AttributeError:
            pass

        try:
            if before.nsfw != after.nsfw:
                em.add_field(name='NSFW', value=f'`{before.nsfw}` **->** `{after.nsfw}`', inline=False)
        except AttributeError:
            pass

        try:
            if before.default_auto_archive_duration != after.default_auto_archive_duration:
                _ = {
                    60: '1 hour',
                    1440: '1 day',
                    4320: '3 days',
                    10080: '1 week'
                }
                em.add_field(
                    name='Default Thread Archive Duration',
                    value=f'`{_[before.default_auto_archive_duration]}` '
                          f'**->** `{_[after.default_auto_archive_duration]}`',
                    inline=False
                )
        except AttributeError:
            pass

        try:
            if before.slowmode_delay != after.slowmode_delay:
                before_slowmode = '0 seconds' if before.slowmode_delay == 0 else utils.time_phaser(before.slowmode_delay)
                after_slowmode = '0 seconds' if after.slowmode_delay == 0 else utils.time_phaser(after.slowmode_delay)
                em.add_field(
                    name='Slowmode Delay',
                    value=f'`{before_slowmode}` **->** `{after_slowmode}`',
                    inline=False
                )
        except AttributeError:
            pass

        try:
            if before.user_limit != after.user_limit:
                em.add_field(
                    name='User Limit',
                    value=f'`{before.user_limit}` **->** `{after.user_limit}`',
                    inline=False
                )
        except AttributeError:
            pass

        if len(em.fields) != 0:
            self.embeds.append(em)


def setup(bot: Ukiyo):
    bot.add_cog(Logs(bot))