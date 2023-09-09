import inspect
import itertools
from textwrap import shorten
from typing import Any, Dict, List, Optional

import disnake
from disnake.ext import commands

import utils
from utils.paginator import RoboPages

from disnake.ext import menus


class GroupHelpPageSource(menus.ListPageSource):
    def __init__(self, group: commands.Group | commands.Cog, commands: List[commands.Command], *, prefix: str, aliases: List[str] = None):
        super().__init__(entries=commands, per_page=6)
        self.group = group
        self.prefix = prefix
        self.title = f'{self.group.qualified_name} Commands'
        self.description = ', '.join(self.group.aliases) if aliases else self.group.description

    async def format_page(self, menu, commands):
        embed = disnake.Embed(title=self.title, description=self.description, color=utils.blurple)

        for command in commands:
            if command.signature:
                signature = f'```{self.prefix}{command.qualified_name} {command.signature}\n```'
            else:
                signature = f'```{self.prefix}{command.qualified_name}\n```'
            embed.add_field(name=signature, value=command.short_doc or 'No help given...', inline=False)

        maximum = self.get_max_pages()
        if maximum > 1:
            embed.set_author(name=f'Page {menu.current_page + 1}/{maximum} ({len(self.entries)} commands)')

        embed.set_footer(text=f'Use "{self.prefix}help <command>" for more info on a command.')
        return embed


class HelpSelectMenu(disnake.ui.Select['HelpMenu']):
    def __init__(self, commands: Dict[commands.Cog, List[commands.Command]], bot: commands.AutoShardedBot):
        super().__init__(
            placeholder='Select a category...',
            min_values=1,
            max_values=1,
            row=0,
        )
        self.commands = commands
        self.bot = bot
        self.__fill_options()

    def __fill_options(self) -> None:
        self.add_option(
            label='Index',
            emoji='\N{WAVING HAND SIGN}',
            value='__index',
            description='The help page showing how to use the bot.',
        )
        for cog, commands in self.commands.items():  # noqa
            if not commands:
                continue
            description = cog.description.split('\n', 1)[0] or None
            if description is not None:
                description = shorten(description, 100)
            emoji = getattr(cog, 'display_emoji', None)
            self.add_option(
                label=cog.qualified_name + ' [' + str(len(list(cog.walk_commands()))) + ']',
                value=cog.qualified_name,
                description=description,
                emoji=emoji
            )

    async def callback(self, interaction: disnake.Interaction):
        assert self.view is not None
        value = self.values[0]
        if value == '__index':
            await self.view.rebind(FrontPageSource(), interaction)
        else:
            cog = self.bot.get_cog(value)
            if cog is None:
                await interaction.response.send_message('Somehow this category does not exist?', ephemeral=True)
                return

            commands = self.commands[cog]
            if not commands:
                await interaction.response.send_message('This category has no commands for you', ephemeral=True)
                return

            source = GroupHelpPageSource(cog, commands, prefix=self.view.ctx.clean_prefix)
            await self.view.rebind(source, interaction)


class HelpMenu(RoboPages):
    def __init__(self, source: menus.PageSource, ctx: commands.Context):
        super().__init__(source, ctx=ctx, compact=True)

    def add_categories(self, commands: Dict[commands.Cog, List[commands.Command]]) -> None:
        self.clear_items()
        self.add_item(HelpSelectMenu(commands, self.ctx.bot))
        self.fill_items()

    async def rebind(self, source: menus.PageSource, interaction: disnake.Interaction) -> None:
        self.source = source
        self.current_page = 0

        await self.source._prepare_once()
        page = await self.source.get_page(0)
        kwargs = await self._get_kwargs_from_page(page)
        self._update_labels(0)
        await interaction.response.edit_message(**kwargs, view=self)


class FrontPageSource(menus.PageSource):
    def is_paginating(self) -> bool:
        # This forces the buttons to appear even in the front page
        return True

    def get_max_pages(self) -> Optional[int]:
        # There's only one actual page in the front page
        # However we need at least 2 to show all the buttons
        return 2

    async def get_page(self, page_number: int) -> Any:
        # The front page is a dummy
        self.index = page_number
        return self

    def format_page(self, menu: HelpMenu, page):
        embed = disnake.Embed(title='Bot Help', color=utils.blurple)
        embed.set_footer(text=f'TIP: You can also use "{"!" if menu.ctx.clean_prefix == "?" else "?"}" as prefix')
        embed.description = inspect.cleandoc(
            f"""
            Hello! Welcome to the help page.
            Use "{menu.ctx.clean_prefix}help <command>" for more info on a command.
            Use "{menu.ctx.clean_prefix}help <category>" for more info on a category.
            Use the dropdown menu below to select a category.

            **NOTE:** Some commands may only work in <#1137494263811285082>
        """
        )

        if self.index == 1:
            entries = (
                ('<argument>', 'This means the argument is __**required**__.'),
                ('[argument]', 'This means the argument is __**optional**__.'),
                ('[A|B]', 'This means that it can be __**either A or B**__.'),
                (
                    '[argument...]',
                    'This means you can have multiple arguments.\n'
                    'Now that you know the basics, it should be noted that...\n'
                    '__**You do not type in the brackets!**__',
                ),
            )

            embed.add_field(name='How do I use this bot?', value='Reading the bot signature is pretty simple.')

            for name, value in entries:
                embed.add_field(name=name, value=value, inline=False)

        return embed


class PaginatedHelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__(
            command_attrs={
                'help': 'Shows help about the bot, a command, or a category',
                'aliases': ('commands', 'cmds')
            }
        )

    async def on_help_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            # Ignore missing permission errors
            if isinstance(error.original, disnake.HTTPException) and error.original.code == 50013:
                return

            await ctx.reraise(error)

    def get_command_signature(self, command):
        parent = command.full_parent_name
        cmd = command.name if not parent else f'{parent} {command.name}'
        if command.signature:
            return f'```{self.context.clean_prefix}{cmd} {command.signature}\n```'
        else:
            return f'```{self.context.clean_prefix}{cmd}\n```'

    async def send_bot_help(self, mapping):
        bot = self.context.bot

        def key(command) -> str:
            cog = command.cog
            return cog.qualified_name if cog else '\U0010ffff'

        entries: List[commands.Command] = await self.filter_commands(bot.walk_commands(), sort=True, key=key)

        all_commands: Dict[commands.Cog, List[commands.Command]] = {}
        for name, children in itertools.groupby(entries, key=key):
            if name == '\U0010ffff':
                continue

            cog: commands.Cog = bot.get_cog(name)

            if cog.qualified_name == 'Nsfw':
                if not self.context.channel.is_nsfw():
                    continue

            all_commands[cog] = sorted(children, key=lambda c: c.qualified_name)

        menu = HelpMenu(FrontPageSource(), ctx=self.context)
        menu.add_categories(all_commands)
        await menu.start(ref=True)

    async def send_cog_help(self, cog: commands.Cog):
        if cog.qualified_name == 'Nsfw':
            if not self.context.channel.is_nsfw():
                return await self.context.send(
                    f'{self.context.denial} Cannot show help for this category in a non-nsfw channel.'
                )

        entries = await self.filter_commands(cog.walk_commands(), sort=True, key=lambda c: c.qualified_name)
        menu = HelpMenu(GroupHelpPageSource(cog, entries, prefix=self.context.clean_prefix), ctx=self.context)
        await menu.start(ref=True)

    def common_command_formatting(self, embed_like, command):
        embed_like.title = self.get_command_signature(command)
        set_aliases = False
        alias = command.aliases
        if alias:
            try:
                embed_like.add_field(name="Aliases", value=", ".join(alias), inline=False)
                set_aliases = True
            except AttributeError:
                pass
        if command.description:
            embed_like.description = f'{command.description}\n\n{command.help}'
        else:
            embed_like.description = command.help or 'No help found...'
        if set_aliases is False:
            if alias:
                embed_like.description += f'\n**Aliases**\n{", ".join(alias)}'

    async def send_command_help(self, command: commands.Command):
        if command.qualified_name.startswith('nsfw'):
            if not self.context.channel.is_nsfw():
                if command.qualified_name != 'nsfw toggle':
                    return await self.context.send(
                        f'{self.context.denial} Cannot show help for this command in a non-nsfw channel.'
                    )

        # No pagination necessary for a single command.
        embed = disnake.Embed(color=utils.blurple)
        self.common_command_formatting(embed, command)
        await self.context.send(embed=embed, reference=self.context.replied_reference)

    async def send_group_help(self, group: commands.Group):
        if group.qualified_name.startswith('nsfw'):
            if not self.context.channel.is_nsfw():
                return await self.context.send(
                    f'{self.context.denial} Cannot show help for this command in a non-nsfw channel.'
                )

        subcommands = list(group.walk_commands())
        if len(subcommands) == 0:
            return await self.send_command_help(group)

        entries = await self.filter_commands(subcommands, sort=True, key=lambda c: c.qualified_name)
        if len(entries) == 0:
            return await self.send_command_help(group)

        source = GroupHelpPageSource(group, entries, prefix=self.context.clean_prefix)
        self.common_command_formatting(source, group)
        menu = HelpMenu(source, ctx=self.context)
        await menu.start(ref=True)