import pytz
from datetime import datetime
from asyncio import TimeoutError
from dateutil.relativedelta import relativedelta

import disnake
from disnake.ext import commands, tasks

import utils
from utils import Birthday, Channels, StaffRoles

from main import Ukiyo


async def timezones_autocomp(inter: disnake.AppCmdInter, timezone: str):
    return utils.finder(timezone, [t.replace('_', ' ') for t in pytz.all_timezones], lazy=False)[:25]


class Birthdays(commands.Cog):
    """Birthday related commands."""

    def __init__(self, bot: Ukiyo):
        self.bot = bot
        self.check_birthday.start()

    @tasks.loop(seconds=5.0)
    async def check_birthday(self):
        entries: list[Birthday] = await self.bot.db.find_sorted('bday', 'next_birthday', 1)
        now = datetime.now()
        for entry in entries[:15]:
            if now >= entry.next_birthday:
                entry.next_birthday += relativedelta(years=1)
                await entry.commit()

                guild = self.bot.get_guild(1131710408542146602)
                channel = guild.get_channel(Channels.birthdays)
                mem = guild.get_member(entry.id)
                _now = datetime.now() + relativedelta(days=3)  # Use this as source so it doesn't fail to say the right age for the people in UTC- timezones.
                now = datetime.now()
                birthday_timezone = pytz.timezone(entry.timezone.replace(' ', '_'))
                offset = birthday_timezone.utcoffset(now)
                seconds = offset.total_seconds()
                next_birthday = entry.next_birthday + relativedelta(seconds=seconds)
                next_birthday = next_birthday.strftime('%d %B %Y')
                age = utils.human_timedelta(entry.birthday_date, source=_now, accuracy=1, suffix=False) \
                    .replace(' years', '') \
                    .replace(' year', '') \
                    .replace(' ', '')

                # Just commenting this part out for now.
                # Might bring it back in the future (with higher age limit obviously).
                # if age == '20':
                #     if mem.id != self.bot._owner_id:
                #         if any(r for r in StaffRoles.all if r in (role.id for role in mem.roles)) is False:
                #             await utils.try_dm(
                #                 mem,
                #                 'Hello! Happy birthday for turning 20 years of age, but sadly, that also means you no longer meet '
                #                 f'the age requirements of `{guild.name}`, therefore, you have been banned (people can\'t age backwards yk).\n'
                #                 'Apologies for the inconvenience, and once again, happy birthday. :tada: :tada:'
                #             )
                #             await self.bot.db.delete('bday', {'_id': mem.id})
                #             return await mem.kick(reason='User birthday and turned 20y/o+')

                em = disnake.Embed(title=f'Happy {age}th birthday {mem.display_name}!!! :tada: :tada:', color=mem.color)
                em.set_image(url='https://cdn.discordapp.com/attachments/938411306762002456/938443264703463514/happy_bday.gif')
                em.set_footer(text=f'Your next birthday is on {next_birthday}')

                msg = await channel.send(mem.mention, embed=em)
                await msg.add_reaction('🍰')

    @check_birthday.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()

    @commands.slash_command(name='birthday')
    async def birthday(self, inter):
        pass

    @birthday.sub_command(name='view')
    async def birthday_view(
        self,
        inter: disnake.AppCmdInter,
        member: disnake.Member = commands.Param(lambda inter: inter.author)
    ):
        """See how much time left there is until the member's birthday, if they set it.

        Parameters
        ----------
        member: The member you wish to see the birthday of.
        """

        entry: Birthday = await self.bot.db.get('bday', member.id)
        if entry is None:
            if member.id == inter.author.id:
                return await inter.send(
                    f'{self.bot.denial} You did not set your birthday.',
                    ephemeral=True
                )
            else:
                return await inter.send(
                    f'{self.bot.denial} `{member.display_name}` did not set their birthday.',
                    ephemeral=True
                )

        _now = datetime.now() + relativedelta(days=3)  # Use this as source so it doesn't fail to say the right age for the people in UTC- timezones.
        age = utils.human_timedelta(entry.birthday_date, source=_now, accuracy=1, suffix=False) \
            .replace(' years', '') \
            .replace(' year', '') \
            .replace(' ', '')

        em = disnake.Embed(title=f'`{member.display_name}`\'s birthday', color=utils.blurple)
        em.add_field(
            'Age',
            age,
            inline=False
        )
        em.add_field(
            'Birthday date',
            entry.birthday_date.strftime('%d %B %Y'),
            inline=False
        )
        em.add_field(
            'Time left until their next birthday',
            utils.human_timedelta(entry.next_birthday, accuracy=6, suffix=False),
            inline=False
        )
        em.add_field(
            'Timezone',
            entry.timezone,
            inline=False
        )
        em.set_footer(text=f'Requested by: {inter.author.display_name}')

        await inter.send(embed=em)

    @birthday.sub_command(name='set')
    async def birthday_set(
        self,
        inter: disnake.AppCmdInter,
        day: int = commands.Param(ge=1, le=31),
        month: int = commands.Param(ge=1, le=12),
        year: int = commands.Param(ge=2003),
        timezone: str = commands.Param(autocomplete=timezones_autocomp)
    ):
        """Set your birthday.

        Parameters
        ----------
        day: The day you were born in.
        month: The month you were born in.
        year: The year you were born in.
        timezone: The capital of the city you live in with your timezone.
        """

        entry: Birthday = await self.bot.db.get('bday', inter.author.id)
        existed = True
        if entry is None:
            existed = False
            entry = Birthday(id=inter.author.id)

        birthday_date = datetime.strptime(f'{day}/{month}/{year}', '%d/%m/%Y')
        entry.birthday_date = birthday_date

        try:
            birthday_timezone = pytz.timezone(timezone.replace(' ', '_'))
        except pytz.UnknownTimeZoneError:
            return await inter.send(
                f'{self.bot.denial} Wrong capital/timezone. Please pick one that has the exact same timezone as yours.',
                ephemeral=True
            )
        entry.timezone = birthday_timezone.zone.replace('_', ' ')

        now = datetime.now()
        offset = birthday_timezone.utcoffset(now)
        seconds = offset.total_seconds()
        next_birthday = birthday_date - relativedelta(year=now.year, seconds=seconds)
        if now > next_birthday:
            next_birthday += relativedelta(years=1)
        entry.next_birthday = next_birthday

        if existed is False:
            await self.bot.db.add('bday', entry)
        else:
            await entry.commit()
        await inter.send('Your birthday has been set')

    @birthday.sub_command(name='remove')
    async def birthday_remove(self, inter: disnake.AppCmdInter):
        """Remove your birthday, if you have it set."""

        entry: Birthday = await self.bot.db.get('bday', inter.author.id)
        if entry is None:
            return await inter.send(
                f'{self.bot.denial} You did not set your birthday.',
                ephemeral=True
            )

        view = utils.ConfirmViewInteraction(inter)
        await inter.send('Are you sure you want to remove your birthday?', view=view)
        await view.wait()
        if view.response is True:
            await self.bot.db.delete('bday', {'_id': inter.author.id})
            await inter.edit_original_message(content='Successfully removed your birthday.', view=view)
        else:
            await inter.edit_original_message(content='Did not remove your birthday.', view=view)

    @birthday.sub_command(name='upcoming')
    async def bday_top(self, inter: disnake.AppCmdInter):
        """See top 5 upcoming birthdays."""

        guild = self.bot.get_guild(1131710408542146602)
        index = 0
        em = disnake.Embed(color=disnake.Color.blurple(), title='***Top `5` upcoming birthdays***\n _ _ ')

        entries: list[Birthday] = await self.bot.db.find_sorted('bday', 'next_birthday', 1)
        for entry in entries[:5]:
            user = guild.get_member(entry.id)
            index += 1
            next_birthday_date = entry.birthday_date.strftime('%d %B %Y').replace(
                str(entry.birthday_date.year), str(entry.next_birthday.year)
            )
            next_birthday = utils.human_timedelta(entry.next_birthday, accuracy=3)
            em.add_field(
                name=f"`{index}`. _ _ _ _ {user.display_name}",
                value=f'Birthday in `{next_birthday}` ( **{next_birthday_date}** )',
                inline=False
            )

        await inter.send(embed=em)

    @commands.slash_command(name='time')
    async def user_time(
        self,
        inter: disnake.AppCmdInter,
        member: disnake.Member = commands.Param(lambda inter: inter.author)
    ):
        """See what the time is for a user. They must have their birthday set for this to work.

        Parameters
        ----------
        member: The member you want to see the time of.
        """

        entry: Birthday = await self.bot.db.get('birthday', member.id)
        if entry is None:
            if member.id == inter.author.id:
                return await inter.send(
                    f'{self.bot.denial} You must set your birthday if you want to see your current time.',
                    ephemeral=True
                )
            else:
                return await inter.send(
                    f'{self.bot.denial} {member.mention} must set their birthday first.',
                    ephemeral=True
                )

        tz = pytz.timezone(entry.timezone.replace(' ', '_'))
        now = datetime.now()
        offset = tz.utcoffset(now) + now
        res = offset.strftime('%d %B %Y, %I:%M %p (%H:%M)')

        em = disnake.Embed(title=f'`{member.display_name}`\'s time information', color=utils.blurple)
        em.add_field('Current Time', res, inline=False)
        em.add_field('Timezone', entry.timezone, inline=False)
        em.set_footer(text=f'Requested by: {inter.author.display_name}')

        await inter.send(embed=em)

    @commands.Cog.listener()
    async def on_member_remove(self, member: disnake.Member):
        if member.guild.id != 1131710408542146602:
            return

        await self.bot.db.delete('bday', {'_id': member.id})


def setup(bot: Ukiyo):
    bot.add_cog(Birthdays(bot))