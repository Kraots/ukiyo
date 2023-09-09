import disnake

import utils

__all__ = ('QuitButton',)


class QuitButton(disnake.ui.View):
    message: disnake.Message

    def __init__(
        self,
        ctx: utils.Context,
        *,
        timeout: float = 180.0,
        delete_after: bool = False,
        label: str = 'Quit'
    ):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.bot = ctx.bot
        self.delete_after = delete_after
        self.message = None

        self.remove_item(self.quit)
        self.quit.label = label
        self.add_item(self.quit)

    async def interaction_check(self, interaction: disnake.MessageInteraction):
        if interaction.author.id != self.ctx.author.id:
            await interaction.response.send_message(
                f'Only **{self.ctx.author.display_name}** can use the buttons on this message!',
                ephemeral=True
            )
            return False
        return True

    async def on_error(self, error, item, inter):
        await self.bot.inter_reraise(inter, item, error)

    async def on_timeout(self):
        try:
            return await self.message.edit(view=None)
        except disnake.HTTPException:
            pass

    @disnake.ui.button(label='Quit', style=disnake.ButtonStyle.red)
    async def quit(self, button: disnake.ui.Button, inter: disnake.Interaction):
        """Deletes the user's message along with the bot's message."""

        await inter.response.defer()
        to_delete = [self.message]
        if self.delete_after is True:
            to_delete.append(self.ctx.message)
        await utils.try_delete(to_delete)
        self.stop()