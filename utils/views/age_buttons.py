import disnake

__all__ = ('AgeButtonRoles',)

AGE_ROLES = {
    '14-17': 1137493531435470939, '18-22': 1137493557863792672, '23-27': 1137493586980646992,
    '28-32': 1137493614096818268, '33-35': 1137493636309856286, '36+': 1137493662490689627
}


class AgeButtonRoles(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @disnake.ui.button(label='14-17', custom_id='ukiyo:age_roles:14-17', row=0, style=disnake.ButtonStyle.blurple)
    async def _14(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        roles = [role for role in interaction.author.roles if role.id not in AGE_ROLES.values()]
        roles.append(interaction.guild.get_role(AGE_ROLES[button.label]))
        await interaction.author.edit(roles=roles, reason='Age role update.')
        await interaction.response.send_message(
            f'I have changed your age role to `{button.label}`', 
            ephemeral=True
        )

    @disnake.ui.button(label='18-22', custom_id='ukiyo:age_roles:18-22', row=0, style=disnake.ButtonStyle.blurple)
    async def _15(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        roles = [role for role in interaction.author.roles if role.id not in AGE_ROLES.values()]
        roles.append(interaction.guild.get_role(AGE_ROLES[button.label]))
        await interaction.author.edit(roles=roles, reason='Age role update.')
        await interaction.response.send_message(
            f'I have changed your age role to `{button.label}`', 
            ephemeral=True
        )

    @disnake.ui.button(label='23-27', custom_id='ukiyo:age_roles:23-27', row=0, style=disnake.ButtonStyle.blurple)
    async def _16(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        roles = [role for role in interaction.author.roles if role.id not in AGE_ROLES.values()]
        roles.append(interaction.guild.get_role(AGE_ROLES[button.label]))
        await interaction.author.edit(roles=roles, reason='Age role update.')
        await interaction.response.send_message(
            f'I have changed your age role to `{button.label}`', 
            ephemeral=True
        )

    @disnake.ui.button(label='28-32', custom_id='ukiyo:age_roles:28-32', row=1, style=disnake.ButtonStyle.blurple)
    async def _17(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        roles = [role for role in interaction.author.roles if role.id not in AGE_ROLES.values()]
        roles.append(interaction.guild.get_role(AGE_ROLES[button.label]))
        await interaction.author.edit(roles=roles, reason='Age role update.')
        await interaction.response.send_message(
            f'I have changed your age role to `{button.label}`', 
            ephemeral=True
        )

    @disnake.ui.button(label='33-35', custom_id='ukiyo:age_roles:33-35', row=1, style=disnake.ButtonStyle.blurple)
    async def _18(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        roles = [role for role in interaction.author.roles if role.id not in AGE_ROLES.values()]
        roles.append(interaction.guild.get_role(AGE_ROLES[button.label]))
        await interaction.author.edit(roles=roles, reason='Age role update.')
        await interaction.response.send_message(
            f'I have changed your age role to `{button.label}`', 
            ephemeral=True
        )

    @disnake.ui.button(label='36+', custom_id='ukiyo:age_roles:36+', row=1, style=disnake.ButtonStyle.blurple)
    async def _19(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        roles = [role for role in interaction.author.roles if role.id not in AGE_ROLES.values()]
        roles.append(interaction.guild.get_role(AGE_ROLES[button.label]))
        await interaction.author.edit(roles=roles, reason='Age role update.')
        await interaction.response.send_message(
            f'I have changed your age role to `{button.label}`', 
            ephemeral=True
        )
