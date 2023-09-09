import disnake

__all__ = (
    'ConfirmView',
    'ConfirmViewDMS',
    'ConfirmViewInteraction'
)


class ConfirmView(disnake.ui.View):
    message: disnake.Message

    """
    This class is a view with `Yes` and `No` buttons,
    this checks which button the user has pressed and returns
    True via the self.response if the button they clicked was
    Yes else False if the button they clicked is No.
    """

    def __init__(
        self,
        ctx,
        new_message: str = 'Time Expired.',
        react_user: disnake.Member = None,
        *,
        remove_view: bool = False,
        timeout=180.0
    ):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.new_message = new_message
        self.member = react_user
        self.response = False
        self.remove_view = remove_view

    async def interaction_check(self, interaction: disnake.MessageInteraction):
        check_for = self.ctx.author.id if self.member is None else self.member.id
        if interaction.author.id not in (check_for, self.ctx.bot._owner_id):
            await interaction.response.send_message(
                f'Only {self.ctx.author.display_name if self.member is None else self.member.display_name} can use the buttons on this message!',
                ephemeral=True
            )
            return False
        return True

    async def on_error(self, error, item, inter):
        await self.bot.inter_reraise(inter, item, error)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
            item.style = disnake.ButtonStyle.grey
        view = None if self.remove_view is True else self
        await self.message.edit(content=self.new_message, embed=None, view=view)

    @disnake.ui.button(label='Yes', style=disnake.ButtonStyle.green)
    async def yes_button(self, button: disnake.ui.Button, inter: disnake.Interaction):
        await inter.response.defer()
        self.response = True
        for item in self.children:
            item.disabled = True
            item.style = disnake.ButtonStyle.grey
            if item.label == button.label:
                item.style = disnake.ButtonStyle.blurple
        view = None if self.remove_view is True else self
        await self.message.edit(view=view)
        self.stop()

    @disnake.ui.button(label='No', style=disnake.ButtonStyle.red)
    async def no_button(self, button: disnake.ui.Button, inter: disnake.Interaction):
        await inter.response.defer()
        for item in self.children:
            item.disabled = True
            item.style = disnake.ButtonStyle.grey
            if item.label == button.label:
                item.style = disnake.ButtonStyle.blurple
        view = None if self.remove_view is True else self
        await self.message.edit(view=view)
        self.stop()


class ConfirmViewDMS(disnake.ui.View):
    message: disnake.Message

    """
    This class is a view with `Yes` and `No` buttons
    which only works in dms, this checks which button the user
    has pressed and returns True via the self.response if the
    button they clicked was Yes else False if the button
    they clicked is No.
    """

    def __init__(self, ctx, *, timeout=180.0, new_message: str = 'Time Expired.'):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.new_message = new_message
        self.response = False

    async def on_error(self, error, item, inter):
        await self.bot.inter_reraise(inter, item, error)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
            item.style = disnake.ButtonStyle.grey
        await self.message.edit(content=self.new_message, embed=None, view=self)

    @disnake.ui.button(label='Yes', style=disnake.ButtonStyle.green)
    async def yes_button(self, button: disnake.ui.Button, inter: disnake.Interaction):
        await inter.response.defer()
        self.response = True
        for item in self.children:
            item.disabled = True
            item.style = disnake.ButtonStyle.grey
            if item.label == button.label:
                item.style = disnake.ButtonStyle.blurple
        await self.message.edit(view=self)
        self.stop()

    @disnake.ui.button(label='No', style=disnake.ButtonStyle.red)
    async def no_button(self, button: disnake.ui.Button, inter: disnake.Interaction):
        await inter.response.defer()
        for item in self.children:
            item.disabled = True
            item.style = disnake.ButtonStyle.grey
            if item.label == button.label:
                item.style = disnake.ButtonStyle.blurple
        await self.message.edit(view=self)
        self.stop()


class ConfirmViewInteraction(disnake.ui.View):
    """
    This class is a view with `Yes` and `No` buttons
    which only works with interactions, this checks which button the user
    has pressed and returns True via the self.response if the
    button they clicked was Yes else False if the button
    they clicked is No.
    """

    def __init__(
            self,
            inter: disnake.MessageInteraction,
            *,
            timeout=180.0,
            new_message: str = 'Time Expired.',
            react_user: disnake.Member = None
        ):
        super().__init__(timeout=timeout)
        self.inter = inter
        self.new_message = new_message
        self.response = False
        self.member = react_user

    async def interaction_check(self, interaction: disnake.MessageInteraction):
        check_for = self.inter.author.id if self.member is None else self.member.id
        if interaction.author.id not in (check_for, interaction.bot._owner_id):
            await interaction.response.send_message(
                f'Only {self.inter.author.display_name if self.member is None else self.member.display_name} '
                'can use the buttons on this message!',
                ephemeral=True
            )
            return False
        return True

    async def on_error(self, error, item, inter):
        await inter.bot.inter_reraise(inter, item, error)

    @disnake.ui.button(label='Yes', style=disnake.ButtonStyle.green)
    async def yes_button(self, button: disnake.ui.Button, inter: disnake.Interaction):
        await inter.response.defer()
        self.response = True
        for item in self.children:
            item.disabled = True
            item.style = disnake.ButtonStyle.grey
            if item.label == button.label:
                item.style = disnake.ButtonStyle.blurple
        self.stop()

    @disnake.ui.button(label='No', style=disnake.ButtonStyle.red)
    async def no_button(self, button: disnake.ui.Button, inter: disnake.Interaction):
        await inter.response.defer()
        for item in self.children:
            item.disabled = True
            item.style = disnake.ButtonStyle.grey
            if item.label == button.label:
                item.style = disnake.ButtonStyle.blurple
        self.stop()