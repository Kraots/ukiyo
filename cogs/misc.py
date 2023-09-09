import time
import psutil

import disnake
from disnake.ext import commands

import utils
from utils import Context

from main import Ukiyo


class Misc(commands.Cog):
    """Miscellaneous commands, basically commands that i have no fucking idea where to fucking put so they just come in this category."""
    def __init__(self, bot: Ukiyo):
        self.bot = bot

    @property
    def display_emoji(self) -> str:
        return '🔧'

    @commands.slash_command(name='rules')
    async def rules(self, inter):
        pass

    @rules.sub_command(name='view')
    async def rules_view(self, inter: disnake.AppCmdInter, rule: int = None):
        """Sends the server's rules. If ``rule`` is given, it will only send that rule.

        Parameters
        ----------
        rule: The number of the rule you want to view.
        """

        entry: utils.Misc = await self.bot.db.get('misc')
        if len(entry.rules) == 0:
            return await inter.send(
                f'{self.bot.denial} There are currently no rules set. Please contact an admin about this!',
                ephemeral=True
            )
        embeds = []

        if rule is None:
            em = disnake.Embed(title='Rules', color=utils.blurple)
            em.set_footer(text='NOTE: Breaking any of these rules will result in a mute, or in the worst case, a ban.')
            for index, rule in enumerate(entry.rules):
                if index in (10, 20, 30, 40, 50):  # Show 10 rules per embed
                    embeds.append(em)
                    em = disnake.Embed(title='Rules', color=utils.blurple)
                    em.set_footer(text='NOTE: Breaking any of these rules will result in a mute, or in the worst case, a ban.')

                if em.description is None:
                    em.description = f'`{index + 1}.` {rule}'
                else:
                    em.description += f'\n\n`{index + 1}.` {rule}'
            embeds.append(em)

        else:
            em = disnake.Embed(title='Rules', color=utils.blurple)
            if rule <= 0:
                return await inter.send(
                    f'{self.bot.denial} Rule cannot be equal or less than `0`',
                    ephemeral=True
                )
            try:
                _rule = entry.rules[rule - 1]
                em.description = f'`{rule}.` {_rule}'
            except IndexError:
                return await inter.send(f'{self.bot.denial} Rule does not exist!', ephemeral=True)
            em.set_footer(text='NOTE: Breaking any of these rules will result in a mute, or in the worst case, a ban.')
            embeds.append(em)

        await inter.send(embeds=embeds)

    @rules.sub_command(name='add')
    async def rules_add(self, inter: disnake.AppCmdInter, rule: str):
        """Adds a rule to the server's rules.

        Parameters
        ----------
        rule: The rule you want to add.
        """

        if not any(r for r in (utils.StaffRoles.owner, utils.StaffRoles.admin) if r in (role.id for role in inter.author.roles)):
            if inter.author.id != self.bot._owner_id:
                await inter.send(
                    f'{self.bot.denial} This command can only be used by admins and above!',
                    ephemeral=True
                )

        entry: utils.Misc = await self.bot.db.get('misc')
        if entry.rules is None:
            entry.rules = [rule]
        else:
            entry.rules += [rule]
            await entry.commit()

        await inter.send(f'> 👌 📝 `{utils.escape_markdown(rule)}` successfully **added** to the rules.')

    @rules.sub_command(name='edit')
    async def server_rules_edit(self, inter: disnake.AppCmdInter, rule: int, new_rule: str):
        """Edits an existing rule.

        Parameters
        ----------
        rule: The number of the rule you want to edit.
        new_rule: The new rule to replace it.
        """

        if not any(r for r in (utils.StaffRoles.owner, utils.StaffRoles.admin) if r in (role.id for role in inter.author.roles)):
            if inter.author.id != self.bot._owner_id:
                await inter.send(
                    f'{self.bot.denial} This command can only be used by admins and above!',
                    ephemeral=True
                )

        entry: utils.Misc = await self.bot.db.get('misc')
        if len(entry.rules) == 0:
            return await inter.send(
                f'{self.bot.denial} There are currently no rules set.',
                ephemeral=True
            )
        elif rule == 0:
            return await inter.send(
                f'{self.bot.denial} Rule cannot be ``0``',
                ephemeral=True
            )

        rule -= 1
        try:
            entry.rules[rule] = new_rule
        except IndexError:
            return await inter.send(
                f'{self.bot.denial} Rule does not exist!',
                ephemeral=True
            )
        await entry.commit()

        await inter.send(f'> 👌 📝 Successfully **edited** rule `{rule + 1}` to `{new_rule}`.')

    @rules.sub_command(name='remove')
    async def server_rules_remove(self, inter: disnake.AppCmdInter, rule: int):
        """Removes a rule from the server's rules by its number.

        Parameters
        ----------
        rule: The number of the rule to remove.
        """

        if not any(r for r in (utils.StaffRoles.owner, utils.StaffRoles.admin) if r in (role.id for role in inter.author.roles)):
            if inter.author.id != self.bot._owner_id:
                await inter.send(
                    f'{self.bot.denial} This command can only be used by admins and above!',
                    ephemeral=True
                )

        entry: utils.Misc = await self.bot.db.get('misc')
        if len(entry.rules) == 0:
            return await inter.send(
                f'{self.bot.denial} There are currently no rules set.',
                ephemeral=True
            )
        else:
            if rule <= 0:
                return await inter.send(
                    f'{self.bot.denial} Rule cannot be equal or less than `0`',
                    ephemeral=True
                )
            try:
                entry.rules.pop(rule - 1)
            except IndexError:
                return await inter.send(
                    f'{self.bot.denial} Rule does not exist!',
                    ephemeral=True
                )
            await entry.commit()

        await inter.send(f'> 👌 Successfully **removed** rule `{rule}`.')

    @rules.sub_command(name='clear')
    async def server_rules_clear(self, inter: disnake.AppCmdInter):
        """Deletes all the rules."""

        if not any(r for r in (utils.StaffRoles.owner,) if r in (role.id for role in inter.author.roles)):
            if inter.author.id != self.bot._owner_id:
                await inter.send(
                    f'{self.bot.denial} This command can only be used by owners!',
                    ephemeral=True
                )

        entry: utils.Misc = await self.bot.db.get('misc')
        if len(entry.rules) == 0:
            return await inter.send(
                f'{self.bot.denial} There are currently no rules set.',
                ephemeral=True
            )
        else:
            entry.rules = []
            await entry.commit()

        await inter.send('> 👌 Successfully **cleared** the rules.')

    @commands.slash_command(name='invite')
    async def invite(self, inter: disnake.AppCmdInter):
        """Sends the invite to this server."""

        await inter.send('https://discord.gg/ckU9WkzGmV')

    @commands.slash_command(name='nickname')
    async def nickname(self, inter):
        pass

    @nickname.sub_command(name='set')
    async def nickname_set(
        self,
        inter: disnake.AppCmdInter,
        new_nickname: str = commands.Param(min_length=4, max_length=32)
    ):
        """Change your nickname.

        Parameters
        ----------
        new_nickname: The new nickname you want to set for yourself.
        """

        if len(new_nickname) < 4:
            return await inter.send(
                f'{self.bot.denial} Nickname must be longer than 4 characters.',
                ephemeral=True
            )
        elif len(new_nickname) > 32:
            return await inter.send(
                f'{self.bot.denial} Nickname must be not be over 32 characters.',
                ephemeral=True
            )
        elif utils.check_string(new_nickname) or utils.check_profanity(new_nickname, bad_words=self.bot.bad_words.keys()):
            return await inter.send(
                f'{self.bot.denial} Cannot change your nickname because the nickname you chose '
                'has too few pingable characters, is a bad word or is too short (minimum is **4**).',
                ephemeral=True
            )

        await inter.author.edit(nick=new_nickname)
        await inter.send(f'Successfully changed your nickname to `{new_nickname}`')

    @nickname.sub_command(name='remove')
    async def nickname_remove(self, inter: disnake.AppCmdInter):
        """Removes your nickname."""

        if len(inter.author.global_name) < 4:
            return await inter.send(
                f'{self.bot.denial} Cannot remove your nickname because your name must be longer than 4 characters.',
                ephemeral=True
            )
        elif len(inter.author.global_name) > 32:
            return await inter.send(
                f'{self.bot.denial} Cannot remove your nickname because your name must be not be over 32 characters.',
                ephemeral=True
            )
        elif utils.check_string(inter.author.global_name) or utils.check_profanity(inter.author.global_name, bad_words=self.bot.bad_words.keys()):
            return await inter.send(
                f'{self.bot.denial} Cannot remove your nickname because your name '
                'has too few pingable characters, is a bad word or is too short (minimum is **4**).',
                ephemeral=True
            )

        await inter.author.edit(nick=None)
        await inter.send('Successfully removed your nickname.')

    @commands.command()
    async def ping(self, ctx: Context):
        """See the bot's ping."""

        ping = disnake.Embed(title="Pong!", description="_Pinging..._", color=utils.blurple)
        start = time.time() * 1000
        msg = await ctx.better_reply(embed=ping)
        end = time.time() * 1000
        ping = disnake.Embed(
            title="Pong!",
            description=f"Websocket Latency: `{(round(self.bot.latency * 1000, 2))}ms`"
            f"\nBot Latency: `{int(round(end-start, 0))}ms`"
            f"\nResponse Time: `{(msg.created_at - ctx.message.created_at).total_seconds()/1000}` ms",
            color=utils.blurple
        )
        ping.set_footer(text=f"Online for {utils.human_timedelta(dt=self.bot.uptime, suffix=False)}")
        await msg.edit(embed=ping)

    @commands.command()
    async def uptime(self, ctx: Context):
        """See how long the bot has been online for."""

        uptime = disnake.Embed(
            description=f"Bot has been online since {utils.format_dt(self.bot.uptime, 'F')} "
                        f"(`{utils.human_timedelta(dt=self.bot.uptime, suffix=False)}`)",
            color=utils.blurple
        )
        uptime.set_footer(text=f'Bot made by: {self.bot._owner}')
        await ctx.better_reply(embed=uptime)

    @commands.command(name='metrics')
    async def show_metrics(self, ctx: Context):
        """Shows the metrics as well as some info about the bot."""

        em = disnake.Embed(title='Metrics', description='_Fetching Metrics..._', colour=utils.invisible)
        start = time.time() * 1000
        msg = await ctx.better_reply(embed=em)
        end = time.time() * 1000

        process = psutil.Process()
        mem = process.memory_full_info()
        cpu_usage = psutil.cpu_percent()
        physical = utils.natural_size(mem.rss)
        threads = process.num_threads()
        pid = process.pid

        prefix_commands = 0
        for _ in self.bot.walk_commands():
            prefix_commands += 1

        slash_commands = 0
        for slash_command in self.bot.slash_commands:
            slash_commands += 1
            for sub_slash_command in slash_command.children.values():
                slash_commands += 1
                if isinstance(sub_slash_command, commands.SubCommandGroup):
                    for sub_cmd in sub_slash_command.children:
                        slash_commands += 1

        extensions = len(self.bot.extensions)

        em = disnake.Embed(title='Metrics', colour=utils.invisible)
        em.add_field(
            name='Ping',
            value=f'Websocket Latency: `{(round(self.bot.latency * 1000, 2))}ms`'
                  f'\nBot Latency: `{int(round(end-start, 0))}ms`'
                  f'\nResponse Time: `{(msg.created_at - ctx.message.created_at).total_seconds()/1000}` ms',
            inline=False
        )
        em.add_field(
            name='Memory Usage',
            value=f'CPU: {cpu_usage}%'
                  f'\nRAM Usage: {physical}'
                  f'\nThreads: {threads}'
                  f'\nPID: {pid}',
            inline=False
        )
        em.add_field(
            name='Extras',
            value=f'Running on commit [``{self.bot.git_hash[:7]}``](https://github.com/Kraots/ukiyo/tree/{self.bot.git_hash})'
                  f'\nPrefix Commands: {prefix_commands}'
                  f'\nSlash Commands: {slash_commands}'
                  f'\nExtensions: {extensions}'
                  f'\nUptime: {utils.human_timedelta(dt=self.bot.uptime, suffix=False)}',
            inline=False
        )

        em.set_footer(
            text=f'Bot made by: {self.bot._owner}',
            icon_url=self.bot.user.display_avatar.url
        )

        await msg.edit(embed=em)

    @commands.command(name='enlarge', aliases=('ee',))
    async def enlarge_emoji(self, ctx: Context, emojis: commands.Greedy[disnake.PartialEmoji]):
        """Enlarges the given emojis. Can be either one or more.

        `emoji` **->** The emojis to enlarge. It's optional and you can also reply to a message with this command to get the emojis from that message.
        **NOTE:** This works for custom emojis only!
        """

        if len(emojis) == 0:
            if ctx.replied_reference is not None:
                reference = await self.bot.reference_to_message(ctx.replied_reference)
                if reference:
                    _emojis = utils.CUSTOM_EMOJI_REGEX.findall(reference.content)
                    if _emojis:
                        for emoji in _emojis:
                            animated = True if emoji[0] != '' else False
                            emojis.append(disnake.PartialEmoji(name=emoji[1], id=emoji[2], animated=animated))
            else:
                return await ctx.reply('Must either give the emojis either reply to a message that has them.')

        if len(emojis) == 0:
            return await ctx.reply('No emojis found.')

        embeds = []
        for emoji in emojis:
            embed = disnake.Embed(
                title=f'Showing emoji `{emoji.name}`',
                color=utils.blurple
            )
            embed.set_image(emoji.url)
            embeds.append(embed)

        paginator = utils.EmbedPaginator(ctx, embeds)
        await paginator.start(ref=True)

    @commands.slash_command(name='member-count')
    async def member_count(self, inter: disnake.AppCmdInter):
        """Shows how many members the server has, as well as how many are verified and how many are not."""

        guild = self.bot.get_guild(1131710408542146602)
        members = len([m for m in guild.members if not m.bot])
        bots = len([b for b in guild.members if b.bot])
        verified = len(await self.bot.db.find('intros'))
        unverified = members - verified

        verified_percentage = round(float(verified * 100 / members), 2)
        unverified_percentage = round(float(unverified * 100 / members), 2)

        em = disnake.Embed(title='Member Count', color=utils.blurple)
        em.add_field(
            name='Total Members',
            value=f'{members:,}',
            inline=False
        )
        em.add_field(
            name='Total Bots',
            value=f'{bots:,}',
            inline=False
        )
        em.add_field(
            name='Verified Members',
            value=f'{verified:,} ({verified_percentage}%)',
            inline=False
        )
        em.add_field(
            name='Unverified Members',
            value=f'{unverified:,} ({unverified_percentage}%)',
            inline=False
        )
        em.set_footer(text=f'Requested by: {inter.author.display_name}')

        await inter.send(embed=em)


def setup(bot: Ukiyo):
    bot.add_cog(Misc(bot))
