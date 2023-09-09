import disnake

__all__ = ('GenderButtonRoles',)

GENDER_ROLES = {
    'Cis Male': 1137491906264322129, 'Cis Female': 1137491987101122691, 'Trans Male': 1137492036866539663,
    'Trans Female': 1137492148502134824, 'Non Binary': 1137492213027323964, 'Other Gender': 1137492685486297259
}


class GenderButtonRoles(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @disnake.ui.button(label='Cis Male', custom_id='ukiyo:gender_roles:Male', row=0, style=disnake.ButtonStyle.blurple)
    async def Cis_Male(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        roles = [role for role in interaction.author.roles if role.id not in GENDER_ROLES.values()]
        roles.append(interaction.guild.get_role(GENDER_ROLES[button.label]))
        await interaction.author.edit(roles=roles, reason='Gender role update.')
        await interaction.response.send_message(
            f'I have changed your gender role to `{button.label}`', 
            ephemeral=True
        )

    @disnake.ui.button(label='Cis Female', custom_id='ukiyo:gender_roles:Female', row=0, style=disnake.ButtonStyle.blurple)
    async def Cis_Female(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        roles = [role for role in interaction.author.roles if role.id not in GENDER_ROLES.values()]
        roles.append(interaction.guild.get_role(GENDER_ROLES[button.label]))
        await interaction.author.edit(roles=roles, reason='Gender role update.')
        await interaction.response.send_message(
            f'I have changed your gender role to `{button.label}`', 
            ephemeral=True
        )

    @disnake.ui.button(label='Trans Male', custom_id='ukiyo:gender_roles:TransMale', row=1, style=disnake.ButtonStyle.blurple)
    async def Trans_Male(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        roles = [role for role in interaction.author.roles if role.id not in GENDER_ROLES.values()]
        roles.append(interaction.guild.get_role(GENDER_ROLES[button.label]))
        await interaction.author.edit(roles=roles, reason='Gender role update.')
        await interaction.response.send_message(
            f'I have changed your gender role to `{button.label}`', 
            ephemeral=True
        )

    @disnake.ui.button(label='Trans Female', custom_id='ukiyo:gender_roles:TransFemale', row=1, style=disnake.ButtonStyle.blurple)
    async def Trans_Female(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        roles = [role for role in interaction.author.roles if role.id not in GENDER_ROLES.values()]
        roles.append(interaction.guild.get_role(GENDER_ROLES[button.label]))
        await interaction.author.edit(roles=roles, reason='Gender role update.')
        await interaction.response.send_message(
            f'I have changed your gender role to `{button.label}`', 
            ephemeral=True
        )

    @disnake.ui.button(label='Non Binary', custom_id='ukiyo:gender_roles:NonBinary', row=2, style=disnake.ButtonStyle.blurple)
    async def Non_Binary(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        roles = [role for role in interaction.author.roles if role.id not in GENDER_ROLES.values()]
        roles.append(interaction.guild.get_role(GENDER_ROLES[button.label]))
        await interaction.author.edit(roles=roles, reason='Gender role update.')
        await interaction.response.send_message(
            f'I have changed your gender role to `{button.label}`', 
            ephemeral=True
        )

    @disnake.ui.button(label='Other Gender', custom_id='ukiyo:gender_roles:OtherGender', row=2, style=disnake.ButtonStyle.blurple)
    async def Other_Gender(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        roles = [role for role in interaction.author.roles if role.id not in GENDER_ROLES.values()]
        roles.append(interaction.guild.get_role(GENDER_ROLES[button.label]))
        await interaction.author.edit(roles=roles, reason='Gender role update.')
        await interaction.response.send_message(
            f'I have changed your gender role to `{button.label}`', 
            ephemeral=True
        )
