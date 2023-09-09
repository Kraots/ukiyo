import disnake

__all__ = ('DMSButtonRoles',)

DMS_ROLES = {
    'DMS: Open': 1137493426447843448, 'DMS: Ask': 1137493465966596156, 'DMS: Closed': 1137493499416150127
}


class DMSButtonRoles(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @disnake.ui.button(label='DMS: Open', custom_id='ukiyo:dms_roles:DMSOpen', row=0, style=disnake.ButtonStyle.blurple)
    async def DMS_Open(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        roles = [role for role in interaction.author.roles if role.id not in DMS_ROLES.values()]
        roles.append(interaction.guild.get_role(DMS_ROLES[button.label]))
        await interaction.author.edit(roles=roles, reason='DMS role update.')
        await interaction.response.send_message(
            f'I have changed your DMS role to `{button.label}`', 
            ephemeral=True
        )

    @disnake.ui.button(label='DMS: Ask', custom_id='ukiyo:dms_roles:DMSAsk', row=0, style=disnake.ButtonStyle.blurple)
    async def DMS_Ask(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        roles = [role for role in interaction.author.roles if role.id not in DMS_ROLES.values()]
        roles.append(interaction.guild.get_role(DMS_ROLES[button.label]))
        await interaction.author.edit(roles=roles, reason='DMS role update.')
        await interaction.response.send_message(
            f'I have changed your DMS role to `{button.label}`', 
            ephemeral=True
        )

    @disnake.ui.button(label='DMS: Closed', custom_id='ukiyo:dms_roles:DMSClosed', row=0, style=disnake.ButtonStyle.blurple)
    async def DMS_Closed(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        roles = [role for role in interaction.author.roles if role.id not in DMS_ROLES.values()]
        roles.append(interaction.guild.get_role(DMS_ROLES[button.label]))
        await interaction.author.edit(roles=roles, reason='DMS role update.')
        await interaction.response.send_message(
            f'I have changed your DMS role to `{button.label}`', 
            ephemeral=True
        )
