import disnake

__all__ = ('SexualityButtonRoles',)

SEXUALITY_ROLES = {
    'Straight': 1137492467151818794, 'Bisexual': 1137492494532235294, 'Gay': 1137492518456524940,
    'Lesbian': 1137492545044222063, 'Pansexual': 1137492599750541352, 'Asexual': 1137492638413619370,
    'Other Sexuality': 1137493277352923296
}


class SexualityButtonRoles(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @disnake.ui.button(label='Straight', custom_id='ukiyo:sexuality_roles:Straight', row=0, style=disnake.ButtonStyle.blurple)
    async def Straight(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        roles = [role for role in interaction.author.roles if role.id not in SEXUALITY_ROLES.values()]
        roles.append(interaction.guild.get_role(SEXUALITY_ROLES[button.label]))
        await interaction.author.edit(roles=roles, reason='Sexuality role update.')
        await interaction.response.send_message(
            f'I have changed your sexuality role to `{button.label}`', 
            ephemeral=True
        )

    @disnake.ui.button(label='Bisexual', custom_id='ukiyo:sexuality_roles:Bisexual', row=0, style=disnake.ButtonStyle.blurple)
    async def Bisexual(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        roles = [role for role in interaction.author.roles if role.id not in SEXUALITY_ROLES.values()]
        roles.append(interaction.guild.get_role(SEXUALITY_ROLES[button.label]))
        await interaction.author.edit(roles=roles, reason='Sexuality role update.')
        await interaction.response.send_message(
            f'I have changed your sexuality role to `{button.label}`', 
            ephemeral=True
        )

    @disnake.ui.button(label='Gay', custom_id='ukiyo:sexuality_roles:Gay', row=0, style=disnake.ButtonStyle.blurple)
    async def Gay(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        roles = [role for role in interaction.author.roles if role.id not in SEXUALITY_ROLES.values()]
        roles.append(interaction.guild.get_role(SEXUALITY_ROLES[button.label]))
        await interaction.author.edit(roles=roles, reason='Sexuality role update.')
        await interaction.response.send_message(
            f'I have changed your sexuality role to `{button.label}`', 
            ephemeral=True
        )

    @disnake.ui.button(label='Lesbian', custom_id='ukiyo:sexuality_roles:Lesbian', row=1, style=disnake.ButtonStyle.blurple)
    async def Lesbian(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        roles = [role for role in interaction.author.roles if role.id not in SEXUALITY_ROLES.values()]
        roles.append(interaction.guild.get_role(SEXUALITY_ROLES[button.label]))
        await interaction.author.edit(roles=roles, reason='Sexuality role update.')
        await interaction.response.send_message(
            f'I have changed your sexuality role to `{button.label}`', 
            ephemeral=True
        )

    @disnake.ui.button(label='Pansexual', custom_id='ukiyo:sexuality_roles:Pansexual', row=1, style=disnake.ButtonStyle.blurple)
    async def Pansexual(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        roles = [role for role in interaction.author.roles if role.id not in SEXUALITY_ROLES.values()]
        roles.append(interaction.guild.get_role(SEXUALITY_ROLES[button.label]))
        await interaction.author.edit(roles=roles, reason='Sexuality role update.')
        await interaction.response.send_message(
            f'I have changed your sexuality role to `{button.label}`', 
            ephemeral=True
        )

    @disnake.ui.button(label='Asexual', custom_id='ukiyo:sexuality_roles:Asexual', row=1, style=disnake.ButtonStyle.blurple)
    async def Asexual(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        roles = [role for role in interaction.author.roles if role.id not in SEXUALITY_ROLES.values()]
        roles.append(interaction.guild.get_role(SEXUALITY_ROLES[button.label]))
        await interaction.author.edit(roles=roles, reason='Sexuality role update.')
        await interaction.response.send_message(
            f'I have changed your sexuality role to `{button.label}`', 
            ephemeral=True
        )

    @disnake.ui.button(label='Other Sexuality', custom_id='ukiyo:sexuality_roles:OtherSexuality', row=2, style=disnake.ButtonStyle.blurple)
    async def Other_Sexuality(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        roles = [role for role in interaction.author.roles if role.id not in SEXUALITY_ROLES.values()]
        roles.append(interaction.guild.get_role(SEXUALITY_ROLES[button.label]))
        await interaction.author.edit(roles=roles, reason='Sexuality role update.')
        await interaction.response.send_message(
            f'I have changed your sexuality role to `{button.label}`', 
            ephemeral=True
        )
