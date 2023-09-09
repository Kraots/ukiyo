import os
import io
import time
import textwrap
import datetime
import contextlib
from traceback import format_exception

import disnake
from disnake.ext import commands

import utils
from utils import Context, TextPage, clean_code, Misc

from jishaku.shell import ShellReader

from dulwich.repo import Repo

from main import Ukiyo


class Developer(commands.Cog):
    """Dev only commands."""
    def __init__(self, bot: Ukiyo):
        self.bot = bot

    async def cog_check(self, ctx: Context):
        if ctx.author.id != self.bot._owner_id:
            raise commands.NotOwner
        return True

    @property
    def display_emoji(self) -> str:
        return '⚒️'

    @commands.command(name='eval', aliases=['e'])
    async def _eval(self, ctx: Context, *, code: str):
        """Evaluate code.

        `code` **->** The code to evaluate.

        **Local Variables**
        \u2800 • ``disnake`` **->** The disnake module.
        \u2800 • ``commands`` **->** The disnake.ext.commands module.
        \u2800 • ``_bot`` **->** The bot instance. (`ukiyo`)
        \u2800 • ``_ctx`` **->** The ``Context`` object of the command.
        \u2800 • ``_channel`` **->** The ``disnake.abc.GuildChannel`` the command is invoked in.
        \u2800 • ``_author`` **->** The ``disnake.Member`` of the command.
        \u2800 • ``_guild`` **->** The ``disnake.Guild`` object the command is invoked in.
        \u2800 • ``_message`` **->** The ``disnake.Message`` object of the command.
        \u2800 • ``utils`` **->** The bot's ``utils`` custom package.
        """

        code = clean_code(code)

        local_variables = {
            "disnake": disnake,
            "commands": commands,
            "_bot": self.bot,
            "_ctx": ctx,
            "_channel": ctx.channel,
            "_author": ctx.author,
            "_guild": ctx.guild,
            "_message": ctx.message,
            "utils": utils
        }
        start = time.perf_counter()

        stdout = io.StringIO()
        try:
            with contextlib.redirect_stdout(stdout):
                exec(
                    f"async def func():\n{textwrap.indent(code, '    ')}", local_variables,
                )

                obj = await local_variables["func"]()
                result = f"{stdout.getvalue()}\n-- {obj}\n"
        except Exception as e:
            result = ("".join(format_exception(e, e, e.__traceback__)))

        end = time.perf_counter()
        took = f"{end-start:.3f}"
        if took == "0.000":
            took = f"{end-start:.7f}"

        if len(result) >= 4000:
            pager = TextPage(
                ctx,
                [result[i: i + 4000] for i in range(0, len(result), 4000)],
                footer=f'Took {took}s',
                quit_delete=True,
                prefix='```py',
                suffix='```'
            )
            return await pager.start()
        em = disnake.Embed(description=f'```py\n{result}\n```')
        em.set_footer(text=f'Took {took}s')
        view = utils.QuitButton(ctx, delete_after=True)
        view.message = await ctx.send(embed=em, view=view)
        data = self.bot.execs.get(ctx.author.id)
        if data is None:
            self.bot.execs[ctx.author.id] = {ctx.command.name: view.message}
        else:
            self.bot.execs[ctx.author.id][ctx.command.name] = view.message

    @commands.command()
    async def shutdown(self, ctx: Context):
        """Closes the bot."""

        await ctx.message.add_reaction(ctx.agree)
        pid = os.getpid()
        os.system(f'kill {pid}')

    @commands.command()
    async def restart(self, ctx: Context):
        """Restarts the bot."""

        await ctx.send("*Restarting...*")
        pid = os.getpid()
        os.system('nohup python3.10 main.py &>> activity.log &')
        os.system(f'kill -9 {pid}')

    @commands.command(name='toggle')
    async def toggle_cmd(self, ctx: Context, *, command: str):
        """Toggle a command on and off.

        `command` **->** The command to disable.
        """

        cmd = self.bot.get_command(command)
        if cmd is None:
            return await ctx.reply('Command not found.')
        elif cmd.qualified_name == 'toggle':
            return await ctx.reply('This command cannot be disabled.')

        data: Misc = await self.bot.db.get('misc')
        if cmd.qualified_name in data.disabled_commands:
            data.disabled_commands.remove(cmd.qualified_name)
            await data.commit()
        else:
            data.disabled_commands.append(cmd.qualified_name)
            await data.commit()
        cmd.enabled = not cmd.enabled

        await ctx.reply(
            f'Successfully **{"enabled" if cmd.enabled is True else "disabled"}** the command `{cmd.qualified_name}`'
        )

    @commands.command(name='history', aliases=('dmhistory',))
    async def dm_history(self, ctx: Context, member: disnake.Member, limit: int = 100):
        """Check the bot's dms with a member.

        `member` **->** The member to check the dms for.
        `limit` **->** The limit of how many messages to look up for. Defaults to 100.
        """

        dm = member.dm_channel or await member.create_dm()
        entries = []
        async for message in dm.history(limit=limit):
            content = message.content or '[<NO TEXT>]'
            entries.append(str(message.author.display_name) + ': ' + content + '\n')

        if not entries:
            return await ctx.reply(f'{ctx.disagree} The user does not have any dms with the bot.')

        title = f'Here\'s my dm history with `{member.display_name}`'
        entries = entries[::-1]
        entries = '\n'.join(entries)
        if len(entries) > 500:
            paginator = TextPage(
                ctx,
                [entries[i: i + 500] for i in range(0, len(entries), 500)],
                quit_delete=True,
                prefix='```yaml',
                suffix='```'
            )
            paginator.embed.color = utils.blurple
            paginator.embed.title = title
            return await paginator.start()
        view = utils.QuitButton(ctx, delete_after=True)
        em = disnake.Embed(color=utils.blurple, title=title, description=f'```yaml\n{entries}\n```')
        view.message = await ctx.send(embed=em, view=view)

    @commands.Cog.listener()
    async def on_socket_event_type(self, event_type: str):
        self.bot.socket_events[event_type] += 1

    @commands.command()
    async def gateway(self, ctx: Context) -> None:
        """Sends current stats from the gateway."""
        em = disnake.Embed(title='Gateway Events', color=utils.blurple)

        total_events = sum(self.bot.socket_events.values())
        events_per_second = total_events / (datetime.datetime.utcnow() - self.bot.uptime).total_seconds()

        em.description = f'Start time: {utils.format_relative(self.bot.uptime)}\n'
        em.description += f'Events per second: `{events_per_second:.2f}`/s\n\u200b'

        for event_type, count in self.bot.socket_events.most_common(25):
            em.add_field(name=event_type, value=f'{count:,}')

        await ctx.reply(embed=em)

    @commands.command(aliases=('accountage',))
    async def accage(self, ctx: Context, days: int = None):
        """Set the minimum account age one must be in order to be allowed in the server.

        `days` **->** The minimum amount of days the user's account's age must be. If not given it will show the current minimum amount of days set.
        """

        entry: Misc = await self.bot.db.get('misc')
        if days is None:
            return await ctx.reply(
                f'The current minimum acount age is set to `{entry.min_account_age}` days.'
            )

        entry.min_account_age = days
        await entry.commit()

        await ctx.reply(
            'Successfully made the minimum account age '
            f'that someone must be in order to join the server `{days}` days.'
        )

    @commands.command(name='bot-invite', aliases=('botinv', 'botinvite', 'binv', 'binvite'))
    async def _bot_invite(self, ctx: Context, bot_id: int = None):
        """Sends the link to add the bot to a server (with all permissions enabled).

        `bot_id` **->** The id of the bot you want the invite for, defaults to ukiyo.
        """

        if bot_id is None:
            bot_id = self.bot.user.id

        bot = self.bot.get_user(bot_id)
        if bot is None:
            return await ctx.reply('Could not find a bot with that id.')

        await ctx.reply(f'Invite for `{bot}`: https://discord.com/oauth2/authorize?client_id={bot_id}&scope=bot&permissions=543246773503')

    @commands.command(name='say')
    async def say_something(self, ctx: Context, *, sentence: str):
        """Make the bot say something.
        
        `sentence` **->** The sentence you want the bot to say.
        """

        await ctx.message.delete()

        await ctx.send(sentence)

    @commands.group(aliases=('git', 'gh'), invoke_without_command=True, case_insensitive=True, hidden=True)
    async def github(self, ctx: Context):
        """This does nothing lol."""

        await ctx.send_help('github')

    @github.command(name='pull')
    async def github_pull(self, ctx: Context):
        """Pull any updates from the github repository."""

        with ShellReader('git pull') as reader:
            content = "```" + reader.highlight
            content += f'\n{reader.ps1} git pull\n\n```'

            em = disnake.Embed(description=content)
            m = await ctx.send(embed=em)

            async for line in reader:
                content = content[:-3]
                content += line + '\n```'
                em.description = content
                await m.edit(embed=em)
        content = content[:-3]
        content += '\n[status] Git pull complete.\n```'
        em.description = content

        r = Repo('.')
        self.bot.git_hash = r.head().decode('utf-8')
        r.close()

        await m.edit(embed=em)


def setup(bot: Ukiyo):
    bot.add_cog(Developer(bot))