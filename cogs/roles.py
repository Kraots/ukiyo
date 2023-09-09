import disnake
from disnake.ext import commands
from disnake.interactions import MessageInteraction

from main import Ukiyo

DMS_ROLES = {
    'DMS: Open': 1137493426447843448, 'DMS: Ask': 1137493465966596156, 'DMS: Closed': 1137493499416150127
}
AGE_ROLES = {
    '14': 1137493531435470939, '15': 1137493557863792672, '16': 1137493586980646992,
    '17': 1137493614096818268, '18': 1137493636309856286, '19': 1137493662490689627
}
GENDER_ROLES = {
    'Cis Male': 1137491906264322129, 'Cis Female': 1137491987101122691, 'Trans Male': 1137492036866539663,
    'Trans Female': 1137492148502134824, 'Non Binary': 1137492213027323964, 'Other Gender': 1137492685486297259
}
SEXUALITY_ROLES = {
    'Straight': 1137492467151818794, 'Bisexual': 1137492494532235294, 'Gay': 1137492518456524940,
    'Lesbian': 1137492545044222063, 'Pansexual': 1137492599750541352, 'Asexual': 1137492638413619370,
    'Other Sexuality': 1137493277352923296
}
PRONOUNS_ROLES = {
    'He/Him': 1137492250037866607, 'She/Her': 1137492291741827122, 'He/They': 1137492329784168488,
    'SHe/They': 1137492372054356068, 'They/Them': 1137492410226724874
}


class RolesDMSSelect(disnake.ui.Select['RolesView']):
    def __init__(self):
        super().__init__(placeholder='Select your DMS status...')
        self.__fill_options()

    def __fill_options(self):
        for value in DMS_ROLES.keys():
            self.add_option(label=value)

    async def callback(self, interaction: disnake.MessageInteraction):
        assert self.view is not None
        value = self.values[0]
        roles = [role for role in interaction.author.roles if role.id not in DMS_ROLES.values()]
        roles.append(interaction.guild.get_role(DMS_ROLES[value]))
        await interaction.author.edit(roles=roles, reason='DMS role update via select menu.')
        await interaction.response.edit_message(content=f'Changed your DMS role to `{value}`')


class RolesAgeSelect(disnake.ui.Select['RolesView']):
    def __init__(self):
        super().__init__(placeholder='Select your age...')
        self.__fill_options()

    def __fill_options(self):
        for value in AGE_ROLES.keys():
            self.add_option(label=value)

    async def callback(self, interaction: disnake.MessageInteraction):
        assert self.view is not None
        value = self.values[0]
        roles = [role for role in interaction.author.roles if role.id not in AGE_ROLES.values()]
        roles.append(interaction.guild.get_role(AGE_ROLES[value]))
        await interaction.author.edit(roles=roles, reason='Age role update via select menu.')
        await interaction.response.edit_message(content=f'Changed your age role to `{value}`')


class RolesGenderSelect(disnake.ui.Select['RolesView']):
    def __init__(self):
        super().__init__(placeholder='Select your gender...')
        self.__fill_options()

    def __fill_options(self):
        for value in GENDER_ROLES.keys():
            self.add_option(label=value)

    async def callback(self, interaction: disnake.MessageInteraction):
        assert self.view is not None
        value = self.values[0]
        roles = [role for role in interaction.author.roles if role.id not in GENDER_ROLES.values()]
        roles.append(interaction.guild.get_role(GENDER_ROLES[value]))
        await interaction.author.edit(roles=roles, reason='Gender role update via select menu.')
        await interaction.response.edit_message(content=f'Changed your gender role to `{value}`')


class RolesSexualitySelect(disnake.ui.Select['RolesView']):
    def __init__(self):
        super().__init__(placeholder='Select your sexuality...')
        self.__fill_options()

    def __fill_options(self):
        for value in SEXUALITY_ROLES.keys():
            self.add_option(label=value)

    async def callback(self, interaction: disnake.MessageInteraction):
        assert self.view is not None
        value = self.values[0]
        roles = [role for role in interaction.author.roles if role.id not in SEXUALITY_ROLES.values()]
        roles.append(interaction.guild.get_role(SEXUALITY_ROLES[value]))
        await interaction.author.edit(roles=roles, reason='Sexuality role update via select menu.')
        await interaction.response.edit_message(content=f'Changed your sexuality role to `{value}`')


class RolesPronounsSelect(disnake.ui.Select['RolesView']):
    def __init__(self):
        super().__init__(placeholder='Select your pronouns...')
        self.__fill_options()

    def __fill_options(self):
        for value in PRONOUNS_ROLES.keys():
            self.add_option(label=value)

    async def callback(self, interaction: disnake.MessageInteraction):
        assert self.view is not None
        value = self.values[0]
        roles = [role for role in interaction.author.roles if role.id not in PRONOUNS_ROLES.values()]
        roles.append(interaction.guild.get_role(PRONOUNS_ROLES[value]))
        await interaction.author.edit(roles=roles, reason='Pronouns role update via select menu.')
        await interaction.response.edit_message(content=f'Changed your pronouns role to `{value}`')


class RolesView(disnake.ui.View):
    def __init__(self, role_type: str):
        super().__init__(timeout=None)
        if role_type == 'DMS':
            self.add_item(RolesDMSSelect())
        elif role_type == 'Age':
            self.add_item(RolesAgeSelect())
        elif role_type == 'Gender':
            self.add_item(RolesGenderSelect())
        elif role_type == 'Sexuality':
            self.add_item(RolesSexualitySelect())
        elif role_type == 'Pronouns':
            self.add_item(RolesPronounsSelect())


class Roles(commands.Cog):
    def __init__(self, bot: Ukiyo):
        self.bot = bot

    @commands.slash_command(name='roles')
    async def roles(
        self,
        inter: disnake.AppCmdInter,
        role_type: str = commands.Param(choices=[
            'DMS', 'Age', 'Gender',
            'Sexuality', 'Pronouns'
        ])
    ):
        """Change your roles.

        Parameters
        ----------
        role_type: The type of role you want to change.
        """

        await inter.send(
            f'Use the select menu below to change your `{role_type}`.',
            view=RolesView(role_type),
            ephemeral=True
        )


def setup(bot: Ukiyo):
    bot.add_cog(Roles(bot))