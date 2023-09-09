import disnake

from utils import Context

__all__ = ('ColoursButtonRoles',)

ALL_COLOURS = {
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

COLOURS_EMOJIS = {
    'Red': '<:red:1150112187956858952>', 'Orange': '<:orange:1150112217690284133>', 'Yellow': '<:yellow:1150112192230858863>',
    'Green': '<:green:1150112198870446132>', 'Blue': '<:blue:1150112194827128922>', 'Purple': '<:purple:1150112186346262538>',
    'Dusky Purple': '<:dusky_purple:1150112196458721343>', 'Pink': '<:pink:1150112183519289426>', 'Turquoise': '<:turquoise:1150112190498615296>',
    'Pastel Red': '<:pastel_red:1150112177731158206>', 'Pastel Orange': '<:pastel_orange:1150112224292118588>', 'Pastel Yellow': '<:pastel_yellow:1150112181736714261>',
    'Pastel Green': '<:pastel_green:1150112567411355728>', 'Pastel Blue': '<:pastel_blue:1150112219187650700>', 'Pastel Purple': '<:pastel_purple:1150112175571091639>',
    'Pastel Pink': '<:pastel_pink:1150112173452972032>', 'Pastel Turquoise': '<:pastel_turquoise:1150112180256116826>', 'Neon Red': '<:neon_red:1150112209226190978>',
    'Neon Orange': '<:neon_orange:1150112463036088450>', 'Neon Yellow': '<:neon_yellow:1150112215110791228>', 'Neon Green': '<:neon_green:1150112201458339902>',
    'Neon Blue': '<:neon_blue:1150112405167288371>', 'Neon Purple': '<:neon_purple:1150112509978750976>', 'Neon Pink': '<:neon_pink:1150112205669404702>',
    'Neon Turquoise': '<:neon_turquoise:1150112520451928200>'
}


class ColourButtonItem(disnake.ui.Button):
    def __init__(self, label, emoji):
        super().__init__(
            label=label,
            emoji=emoji,
            custom_id=f'ukiyo:colours:{label.replace(" ", "")}'
        )

    async def callback(self, interaction: disnake.MessageInteraction):
        roles = [role for role in interaction.author.roles if role.id not in ALL_COLOURS.values()]
        roles.append(interaction.guild.get_role(ALL_COLOURS[self.label]))
        await interaction.author.edit(roles=roles, reason='Colour role update via buttons.')
        await interaction.send(f'I have changed your colour to `{self.label}`', ephemeral=True)


class ColoursButtonRoles(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        for colour_name in ALL_COLOURS.keys():
            self.add_item(ColourButtonItem(colour_name, COLOURS_EMOJIS[colour_name]))

    async def start_new_views(self, ctx: Context, message: str):
        self.clear_items()

        # Since we only have 25 colours that means we can just iterate over
        # in a range of 5 each time increasing the index with 5 so that next
        # iteration it takes from the next colour and the 5 next and so on.
        index = 0
        for _ in range(5):
            for colour_name in list(ALL_COLOURS.keys())[index:index + 5]:
                self.add_item(ColourButtonItem(colour_name, COLOURS_EMOJIS[colour_name]))

            index += 5
            await ctx.send(message, view=self)
            self.clear_items()