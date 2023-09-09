from typing import Any, Dict, Optional, List
import asyncio

import disnake
from disnake import MessageInteraction
from disnake.ext import menus

from utils import Context, try_delete

__all__ = (
    'RoboPages',
    'FieldPageSource',
    'TextPageSource',
    'TextPage',
    'SimplePageSource',
    'SimplePages',
    'EmbedPaginator',
    'RawSimplePageSource',
    'RawSimplePages'
)


class RoboPages(disnake.ui.View):
    def __init__(
        self,
        source: menus.PageSource,
        *,
        ctx: Context,
        check_embeds: bool = True,
        compact: bool = False,
        quit_delete: bool = False,
    ):
        super().__init__()
        self.source: menus.PageSource = source
        self.check_embeds: bool = check_embeds
        self.ctx: Context = ctx
        self.message: Optional[disnake.Message] = None
        self.current_page: int = 0
        self.compact: bool = compact
        self.quit_delete: bool = quit_delete
        self.input_lock = asyncio.Lock()
        self.clear_items()
        self.fill_items()

    def fill_items(self) -> None:
        if not self.compact:
            self.numbered_page.row = 1
            self.stop_pages.row = 1

        if self.source.is_paginating():
            max_pages = self.source.get_max_pages()
            use_last_and_first = max_pages is not None and max_pages >= 2
            if use_last_and_first:
                self.add_item(self.go_to_first_page)
            self.add_item(self.go_to_previous_page)
            if not self.compact:
                self.add_item(self.go_to_current_page)
            self.add_item(self.go_to_next_page)
            if use_last_and_first:
                self.add_item(self.go_to_last_page)
            if not self.compact:
                self.add_item(self.numbered_page)
            self.add_item(self.stop_pages)

    async def _get_kwargs_from_page(self, page: int) -> Dict[str, Any]:
        value = await disnake.utils.maybe_coroutine(self.source.format_page, self, page)
        if isinstance(value, dict):
            return value
        elif isinstance(value, str):
            return {'content': value, 'embed': None}
        elif isinstance(value, disnake.Embed):
            return {'embed': value, 'content': None}
        else:
            return {}

    async def show_page(self, interaction: MessageInteraction, page_number: int) -> None:
        page = await self.source.get_page(page_number)
        self.current_page = page_number
        kwargs = await self._get_kwargs_from_page(page)
        self._update_labels(page_number)
        if kwargs:
            if interaction.response.is_done():
                if self.message:
                    await self.message.edit(**kwargs, view=self)
            else:
                await interaction.response.edit_message(**kwargs, view=self)

    def _update_labels(self, page_number: int) -> None:
        self.go_to_first_page.disabled = page_number == 0
        if self.compact:
            max_pages = self.source.get_max_pages()
            self.go_to_last_page.disabled = max_pages is None or (page_number + 1) >= max_pages
            self.go_to_next_page.disabled = max_pages is not None and (page_number + 1) >= max_pages
            self.go_to_previous_page.disabled = page_number == 0
            return

        self.go_to_current_page.label = str(page_number + 1)
        self.go_to_previous_page.label = str(page_number)
        self.go_to_next_page.label = str(page_number + 2)
        self.go_to_next_page.disabled = False
        self.go_to_previous_page.disabled = False
        self.go_to_first_page.disabled = False

        max_pages = self.source.get_max_pages()
        if max_pages is not None:
            self.go_to_last_page.disabled = (page_number + 1) >= max_pages
            if (page_number + 1) >= max_pages:
                self.go_to_next_page.disabled = True
                self.go_to_next_page.label = '…'
            if page_number == 0:
                self.go_to_previous_page.disabled = True
                self.go_to_previous_page.label = '…'

    async def show_checked_page(self, interaction: MessageInteraction, page_number: int) -> None:
        max_pages = self.source.get_max_pages()
        try:
            if max_pages is None:
                # If it doesn't give maximum pages, it cannot be checked
                await self.show_page(interaction, page_number)
            elif max_pages > page_number >= 0:
                await self.show_page(interaction, page_number)
        except IndexError:
            # An error happened that can be handled, so ignore it.
            pass

    async def interaction_check(self, interaction: MessageInteraction) -> bool:
        if interaction.user and interaction.user.id in (self.ctx.bot._owner_id, self.ctx.author.id):
            return True
        await interaction.response.send_message(
            'This pagination menu cannot be controlled by you, sorry!',
            ephemeral=True
        )
        return False

    async def on_timeout(self) -> None:
        await self.message.edit(view=None)

    async def on_error(
        self, error: Exception, item: disnake.ui.Item, interaction: MessageInteraction
    ) -> None:
        if interaction.response.is_done():
            await interaction.followup.send('An unknown error occurred, sorry', ephemeral=True)
        else:
            await interaction.response.send_message(
                'An unknown error occurred, sorry', ephemeral=True
            )
        await self.ctx.bot.inter_reraise(self.ctx.bot, interaction, item, error)

    async def start(self, *, ref: bool = False) -> None:
        await self.source._prepare_once()
        page = await self.source.get_page(0)
        kwargs = await self._get_kwargs_from_page(page)
        self._update_labels(0)
        if ref is False:
            self.message = await self.ctx.send(**kwargs, view=self)
        else:
            self.message = await self.ctx.send(**kwargs, view=self, reference=self.ctx.replied_reference)

    @disnake.ui.button(label='≪', style=disnake.ButtonStyle.grey)
    async def go_to_first_page(self, button: disnake.ui.Button, interaction: MessageInteraction):
        """Go to the first page."""

        await self.show_page(interaction, 0)

    @disnake.ui.button(label='Back', style=disnake.ButtonStyle.blurple)
    async def go_to_previous_page(self, button: disnake.ui.Button, interaction: MessageInteraction):
        """Go to the previous page."""

        await self.show_checked_page(interaction, self.current_page - 1)

    @disnake.ui.button(label='Current', style=disnake.ButtonStyle.grey, disabled=True)
    async def go_to_current_page(self, button: disnake.ui.Button, interaction: MessageInteraction):
        pass

    @disnake.ui.button(label='Next', style=disnake.ButtonStyle.blurple)
    async def go_to_next_page(self, button: disnake.ui.Button, interaction: MessageInteraction):
        """Go to the next page."""

        await self.show_checked_page(interaction, self.current_page + 1)

    @disnake.ui.button(label='≫', style=disnake.ButtonStyle.grey)
    async def go_to_last_page(self, button: disnake.ui.Button, interaction: MessageInteraction):
        """Go to the last page."""

        # The call here is safe because it's guarded by skip_if
        await self.show_page(interaction, self.source.get_max_pages() - 1)

    @disnake.ui.button(label='Skip to page...', style=disnake.ButtonStyle.grey)
    async def numbered_page(self, button: disnake.ui.Button, interaction: MessageInteraction):
        """Lets you type a page number to go to."""

        if self.input_lock.locked():
            await interaction.response.send_message(
                'Already waiting for your response...', ephemeral=True
            )
            return

        if self.message is None:
            return

        async with self.input_lock:
            channel = self.message.channel
            author_id = interaction.user and interaction.user.id
            await interaction.response.send_message(
                'What page do you want to go to?', ephemeral=True
            )

            def message_check(m):
                return m.author.id == author_id and channel == m.channel and m.content.isdigit()

            try:
                msg = await self.ctx.bot.wait_for('message', check=message_check, timeout=30.0)
            except asyncio.TimeoutError:
                await interaction.followup.send('Took too long.', ephemeral=True)
                await asyncio.sleep(5)
            else:
                page = int(msg.content)
                await try_delete(msg)
                await self.show_checked_page(interaction, page - 1)

    @disnake.ui.button(label='Quit', style=disnake.ButtonStyle.red)
    async def stop_pages(self, button: disnake.ui.Button, interaction: MessageInteraction):
        """Stops the pagination session."""

        await interaction.response.defer()
        await interaction.delete_original_message()
        if self.quit_delete:
            await try_delete(self.ctx.message)
        self.stop()


class FieldPageSource(menus.ListPageSource):
    """A page source that requires (field_name, field_value) tuple items."""

    def __init__(self, entries, *, per_page=12):
        super().__init__(entries, per_page=per_page)
        self.embed = disnake.Embed(colour=disnake.Colour.blurple())

    async def format_page(self, menu, entries):
        self.embed.clear_fields()

        for key, value in entries:
            self.embed.add_field(name=key, value=value, inline=False)

        maximum = self.get_max_pages()
        if maximum > 1:
            text = f'Page {menu.current_page + 1}/{maximum} ({len(self.entries)} entries)'
            self.embed.set_footer(text=text)

        return self.embed


class TextPageSource(menus.ListPageSource):
    def __init__(self, entries, *, prefix: str = '', suffix: str = '', has_footer: bool = False):
        super().__init__(entries, per_page=1)
        self.initial_page = True
        self.prefix = prefix
        self.suffix = suffix
        self.has_footer = has_footer

    async def format_page(self, menu, entries):
        maximum = self.get_max_pages()
        if maximum > 1:
            fmt = f'Page {menu.current_page + 1}/{maximum}'
            if self.has_footer is True:
                menu.embed.title = fmt
            else:
                menu.embed.set_footer(text=fmt)

        menu.embed.description = f'{self.prefix}\n{entries}\n{self.suffix}'
        return menu.embed


class TextPage(RoboPages):
    def __init__(
        self,
        ctx,
        entries,
        *,
        footer: str = None,
        quit_delete: bool = False,
        prefix: str = '',
        suffix: str = ''
    ):
        has_footer = False
        if footer is not None:
            has_footer = True
        super().__init__(
            TextPageSource(entries, prefix=prefix, suffix=suffix, has_footer=has_footer),
            ctx=ctx, compact=True, quit_delete=quit_delete
        )
        self.embed = disnake.Embed()
        if footer is not None:
            self.embed.set_footer(text=footer)


class SimplePageSource(menus.ListPageSource):
    def __init__(self, entries, *, per_page=12, entries_name='entries', perma_desc=None):
        super().__init__(entries, per_page=per_page)
        self.initial_page = True
        self.entries_name = entries_name
        self.perma_desc = perma_desc

    async def format_page(self, menu, entries):
        pages = []
        for index, entry in enumerate(entries, start=menu.current_page * self.per_page):
            pages.append(f'`{index + 1}.` {entry}')

        maximum = self.get_max_pages()
        if maximum > 1:
            footer = f'Page {menu.current_page + 1}/{maximum} ({len(self.entries)} {self.entries_name})'
            menu.embed.set_footer(text=footer)

        if self.perma_desc:
            menu.embed.description = self.perma_desc
            menu.embed.description += '\n'.join(pages)
        else:
            menu.embed.description = '\n'.join(pages)

        return menu.embed


class SimplePages(RoboPages):
    """A simple pagination session reminiscent of the old Pages interface.

    Basically an embed with some normal formatting.
    """

    def __init__(
        self, ctx, entries, *, per_page=5, color=None,
        compact=False, entries_name='entries',
        perma_desc=None
    ):
        super().__init__(SimplePageSource(
            entries, per_page=per_page, entries_name=entries_name,
            perma_desc=perma_desc
        ),
            ctx=ctx, compact=compact
        )
        if color is None:
            color = disnake.Color.blurple()
        self.embed = disnake.Embed(colour=color)


class RawSimplePageSource(menus.ListPageSource):
    def __init__(self, entries, *, per_page=12):
        super().__init__(entries, per_page=per_page)
        self.initial_page = True

    async def format_page(self, menu, entries):
        pages = []
        for index, entry in enumerate(entries, start=menu.current_page * self.per_page):
            pages.append(str(entry))

        maximum = self.get_max_pages()
        if maximum > 1:
            footer = f'Page {menu.current_page + 1}/{maximum} ({len(self.entries)} entries)'
            menu.embed.set_footer(text=footer)

        menu.embed.description = '\n'.join(pages)
        return menu.embed


class RawSimplePages(RoboPages):
    """Same as SimplePages but without enumerating them automatically."""

    def __init__(self, ctx, entries, *, per_page=5, color=None, compact=False):
        super().__init__(RawSimplePageSource(entries, per_page=per_page), ctx=ctx, compact=compact)
        if color is None:
            color = disnake.Color.blurple()
        self.embed = disnake.Embed(colour=color)


class EmbedPaginator(disnake.ui.View):
    def __init__(
        self,
        ctx: Context,
        embeds: List[disnake.Embed],
        *,
        timeout: float = 180.0
    ):
        super().__init__(timeout=timeout)
        self.ctx: Context = ctx
        self.embeds: List[disnake.Embed] = embeds

        self.current_page = 0

    async def interaction_check(self, interaction: MessageInteraction) -> bool:
        if interaction.user and interaction.user.id in (self.ctx.bot._owner_id, self.ctx.author.id):
            return True
        await interaction.response.send_message(
            'This pagination menu cannot be controlled by you, sorry!',
            ephemeral=True
        )
        return False

    async def on_timeout(self) -> None:
        if self.message:
            await self.message.edit(view=None)

    async def show_page(self, inter: MessageInteraction, page_number: int):
        if (
            (page_number < 0) or
            (page_number > len(self.embeds) - 1)
        ):
            if not inter.response.is_done():
                await inter.response.defer()
            return
        self.current_page = page_number
        embed = self.embeds[page_number]
        embed.set_footer(text=f'Page {self.current_page + 1}/{len(self.embeds)}')
        if inter.response.is_done():
            await self.message.edit(embed=embed)
        else:
            await inter.response.edit_message(embed=embed)

    @disnake.ui.button(label='≪', style=disnake.ButtonStyle.grey)
    async def go_to_first_page(self, button: disnake.ui.Button, interaction: MessageInteraction):
        """Go to the first page."""

        await self.show_page(interaction, 0)

    @disnake.ui.button(label='Back', style=disnake.ButtonStyle.blurple)
    async def go_to_previous_page(self, button: disnake.ui.Button, interaction: MessageInteraction):
        """Go to the previous page."""

        await self.show_page(interaction, self.current_page - 1)

    @disnake.ui.button(label='Next', style=disnake.ButtonStyle.blurple)
    async def go_to_next_page(self, button: disnake.ui.Button, interaction: MessageInteraction):
        """Go to the next page."""

        await self.show_page(interaction, self.current_page + 1)

    @disnake.ui.button(label='≫', style=disnake.ButtonStyle.grey)
    async def go_to_last_page(self, button: disnake.ui.Button, interaction: MessageInteraction):
        """Go to the last page."""

        await self.show_page(interaction, len(self.embeds) - 1)

    @disnake.ui.button(label='Quit', style=disnake.ButtonStyle.red)
    async def stop_pages(self, button: disnake.ui.Button, interaction: MessageInteraction):
        """Stops the pagination session."""

        await interaction.response.defer()
        await interaction.delete_original_message()
        self.stop()

    async def start(self, *, ref: bool = False):
        """Start paginating over the embeds."""

        if ref is False:
            method = self.ctx.send
        elif ref is True:
            method = self.ctx.better_reply

        if len(self.embeds) == 1:
            return await method(embed=self.embeds[0])

        embed = self.embeds[0]
        embed.set_footer(text=f'Page 1/{len(self.embeds)}')
        self.message = await method(embed=embed, view=self)