import disnake
from disnake.ext import commands

from main import Ukiyo


class ColoursSelect(disnake.ui.Select['ColoursView']):
    def __init__(self):
        super().__init__(placeholder='Select your colour...')
        self.__fill_options()

    def __fill_options(self):
        self.add_option(label='Red', emoji='<:red:1150112187956858952>')
        self.add_option(label='Orange', emoji='<:orange:1150112217690284133>')
        self.add_option(label='Yellow', emoji='<:yellow:1150112192230858863>')
        self.add_option(label='Green', emoji='<:green:1150112198870446132>')
        self.add_option(label='Blue', emoji='<:blue:1150112194827128922>')
        self.add_option(label='Purple', emoji='<:purple:1150112186346262538>')
        self.add_option(label='Dusky Purple', emoji='<:dusky_purple:1150112196458721343>')
        self.add_option(label='Pink', emoji='<:pink:1150112183519289426>')
        self.add_option(label='Turquoise', emoji='<:turquoise:1150112190498615296>')
        self.add_option(label='Pastel Red', emoji='<:pastel_red:1150112177731158206>')
        self.add_option(label='Pastel Orange', emoji='<:pastel_orange:1150112224292118588>')
        self.add_option(label='Pastel Yellow', emoji='<:pastel_yellow:1150112181736714261>')
        self.add_option(label='Pastel Green', emoji='<:pastel_green:1150112567411355728>')
        self.add_option(label='Pastel Blue', emoji='<:pastel_blue:1150112219187650700>')
        self.add_option(label='Pastel Purple', emoji='<:pastel_purple:1150112175571091639>')
        self.add_option(label='Pastel Pink', emoji='<:pastel_pink:1150112173452972032>')
        self.add_option(label='Pastel Turquoise', emoji='<:pastel_turquoise:1150112180256116826>')
        self.add_option(label='Neon Red', emoji='<:neon_red:1150112209226190978>')
        self.add_option(label='Neon Orange', emoji='<:neon_orange:1150112463036088450>')
        self.add_option(label='Neon Yellow', emoji='<:neon_yellow:1150112215110791228>')
        self.add_option(label='Neon Green', emoji='<:neon_green:1150112201458339902>')
        self.add_option(label='Neon Blue', emoji='<:neon_blue:1150112405167288371>')
        self.add_option(label='Neon Purple', emoji='<:neon_purple:1150112509978750976>')
        self.add_option(label='Neon Pink', emoji='<:neon_pink:1150112205669404702>')
        self.add_option(label='Neon Turquoise', emoji='<:neon_turquoise:1150112520451928200>')

    async def callback(self, interaction: disnake.MessageInteraction):
        assert self.view is not None
        value = self.values[0]
        roles = [role for role in interaction.author.roles if role.id not in self.view.all_colours.values()]
        roles.append(interaction.guild.get_role(self.view.all_colours[value]))
        await interaction.author.edit(roles=roles, reason='Colour role update via select menu.')
        await interaction.response.edit_message(content=f'Changed your colour to `{value}`')


class ColoursView(disnake.ui.View):
    all_colours = {
        'Red': 1132430387126218852, 'Orange': 1132430492688457858, 'Yellow': 1132430560770408639,
        'Green': 1132430639833022595, 'Blue': 1132430752060031126, 'Purple': 1132430826127233034,
        'Dusky Purple': 1132435934055518308, 'Pink': 1132430912768983121, 'Turquoise': 1132432651584798911,
        'Pastel Red': 1132430980578299954, 'Pastel Orange': 1132431271264526366, 'Pastel Yellow': 1132431618083143751,
        'Pastel Green': 1132431728468836392, 'Pastel Blue': 1132431909461434429, 'Pastel Purple': 1132432331551015104,
        'Pastel Pink': 1132432491077173312, 'Pastel Turquoise': 1132432744434126939, 'Neon Red': 1132432990790758460,
        'Neon Orange': 1132433117311934564, 'Neon Yellow': 1132433413962469436, 'Neon Green': 1132435270151721100,
        'Neon Blue': 1132435125607600140, 'Neon Purple': 1132435446660603914, 'Neon Pink': 1132435588662952027,
        'Neon Turquoise': 1132435809723760712
    }

    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ColoursSelect())


class Colours(commands.Cog):
    def __init__(self, bot: Ukiyo):
        self.bot = bot

    @commands.slash_command(name='colours')
    async def colours(self, inter: disnake.AppCmdInter):
        """Change your colour."""

        await inter.send(
            'Use the select menu below to change your colour.',
            view=ColoursView(),
            ephemeral=True
        )


def setup(bot: Ukiyo):
    bot.add_cog(Colours(bot))