import disnake

__all__ = ('PronounsButtonRoles',)

PRONOUNS_ROLES = {
    'He/Him': 1137492250037866607, 'She/Her': 1137492291741827122, 'He/They': 1137492329784168488,
    'She/They': 1137492372054356068, 'They/Them': 1137492410226724874
}


class PronounsButtonRoles(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @disnake.ui.button(label='He/Him', custom_id='ukiyo:pronouns_roles:HeHim', row=0, style=disnake.ButtonStyle.blurple)
    async def He_Him(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        roles = [role for role in interaction.author.roles if role.id not in PRONOUNS_ROLES.values()]
        roles.append(interaction.guild.get_role(PRONOUNS_ROLES[button.label]))
        await interaction.author.edit(roles=roles, reason='Pronouns role update.')
        await interaction.response.send_message(
            f'I have changed your pronouns role to `{button.label}`', 
            ephemeral=True
        )

    @disnake.ui.button(label='She/Her', custom_id='ukiyo:pronouns_roles:SheHer', row=0, style=disnake.ButtonStyle.blurple)
    async def She_Her(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        roles = [role for role in interaction.author.roles if role.id not in PRONOUNS_ROLES.values()]
        roles.append(interaction.guild.get_role(PRONOUNS_ROLES[button.label]))
        await interaction.author.edit(roles=roles, reason='Pronouns role update.')
        await interaction.response.send_message(
            f'I have changed your pronouns role to `{button.label}`', 
            ephemeral=True
        )

    @disnake.ui.button(label='He/They', custom_id='ukiyo:pronouns_roles:HeThey', row=1, style=disnake.ButtonStyle.blurple)
    async def He_They(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        roles = [role for role in interaction.author.roles if role.id not in PRONOUNS_ROLES.values()]
        roles.append(interaction.guild.get_role(PRONOUNS_ROLES[button.label]))
        await interaction.author.edit(roles=roles, reason='Pronouns role update.')
        await interaction.response.send_message(
            f'I have changed your pronouns role to `{button.label}`', 
            ephemeral=True
        )

    @disnake.ui.button(label='She/They', custom_id='ukiyo:pronouns_roles:SheThey', row=1, style=disnake.ButtonStyle.blurple)
    async def She_They(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        roles = [role for role in interaction.author.roles if role.id not in PRONOUNS_ROLES.values()]
        roles.append(interaction.guild.get_role(PRONOUNS_ROLES[button.label]))
        await interaction.author.edit(roles=roles, reason='Pronouns role update.')
        await interaction.response.send_message(
            f'I have changed your pronouns role to `{button.label}`', 
            ephemeral=True
        )

    @disnake.ui.button(label='They/Them', custom_id='ukiyo:pronouns_roles:TheyThem', row=2, style=disnake.ButtonStyle.blurple)
    async def They_Them(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        roles = [role for role in interaction.author.roles if role.id not in PRONOUNS_ROLES.values()]
        roles.append(interaction.guild.get_role(PRONOUNS_ROLES[button.label]))
        await interaction.author.edit(roles=roles, reason='Pronouns role update.')
        await interaction.response.send_message(
            f'I have changed your pronouns role to `{button.label}`', 
            ephemeral=True
        )