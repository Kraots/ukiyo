from datetime import datetime

import disnake
from disnake.ext import commands

import utils
from utils import Context, Marriage

from main import Ukiyo


class Marriages(commands.Cog):
    """Marriage commands."""
    def __init__(self, bot: Ukiyo):
        self.bot = bot
        self.currently_marrying: bool = False
        self.currently_divorcing: bool = False
        self.currently_adopting: bool = False
        self.currently_unadopting: bool = False

    @commands.slash_command(name='marry')
    async def marry(self, inter: disnake.AppCmdInter, member: disnake.Member):
        """Marry the member if they want to and if you're/they're not taken by somebody else already.

        Parameters
        ----------
        member: The member you want to marry.
        """

        if self.currently_marrying is True:
            return await inter.send(
                'Uh oh.. looks like someone is already trying to marry! Wait for them to finish.',
                ephemeral=True
            )
        self.currently_marrying = True

        if inter.author == member:
            self.currently_marrying = False
            return await inter.send(
                f'{self.bot.denial} You cannot marry yourself.',
                ephemeral=True
            )
        elif member.bot and inter.author.id != self.bot._owner_id:
            self.currently_marrying = False
            return await inter.send(
                f'{self.bot.denial} You cannot marry bots.',
                ephemeral=True
            )

        data1: Marriage = await self.bot.db.get('marriage', inter.author.id)
        guild = self.bot.get_guild(1131710408542146602)
        if data1 and data1.married_to != 0:
            self.currently_marrying = False
            mem = guild.get_member(data1.married_to)
            return await inter.send(f'{self.bot.denial} You are already married to {mem.mention}')
        elif data1 and member.id in data1.adoptions:
            self.currently_marrying = False
            return await inter.send(
                f'{self.bot.denial} You cannot marry the person that you adopted.',
                ephemeral=True
            )

        data2: Marriage = await self.bot.db.get('marriage', member.id)
        if data2 and data2.married_to != 0:
            self.currently_marrying = False
            mem = guild.get_member(data2.married_to)
            return await inter.send(
                f'{self.bot.denial} `{member.display_name}` is already married to {mem.mention}'
            )
        elif data2 and inter.author.id in data2.adoptions:
            self.currently_marrying = False
            return await inter.send(
                f'{self.bot.denial} You cannot marry the person that adopted you.',
                ephemeral=True
            )
        elif member.id == self.bot._owner_id:
            self.currently_marrying = False
            return await inter.send(f'{self.bot.denial} No.', ephemeral=True)

        view = utils.ConfirmViewInteraction(
            inter,
            new_message=f'{self.bot.denial} {member.mention} Did not react in time.',
            react_user=member
        )
        await inter.send(
            f'{member.mention} do you want to marry {inter.author.mention}?',
            view=view
        )
        await view.wait()
        if view.response is True:
            now = datetime.utcnow()

            if data1 is None:
                await self.bot.db.add('marriages', Marriage(
                    id=inter.author.id,
                    married_to=0,
                    married_since=utils.FIRST_JANUARY_1970,
                    adoptions=[]
                ))
                data1 = await self.bot.db.get('marriage', inter.author.id)

            if data2 is None:
                await self.bot.db.add('marriages', Marriage(
                    id=member.id,
                    married_to=0,
                    married_since=utils.FIRST_JANUARY_1970,
                    adoptions=[]
                ))
                data2 = await self.bot.db.get('marriage', member.id)

            data1.married_to = member.id
            data1.married_since = now
            for adoption in data2.adoptions:
                if adoption not in data1.adoptions:
                    data1.adoptions.append(adoption)
            await data1.commit()

            data2.married_to = inter.author.id
            data2.married_since = now
            for adoption in data1.adoptions:
                if adoption not in data2.adoptions:
                    data2.adoptions.append(adoption)
            await data2.commit()

            await inter.delete_original_response()
            await inter.send(
                f'`{inter.author.display_name}` married `{member.display_name}`!!! :heart: :tada: :tada:'
            )
            self.currently_marrying = False

        elif view.response is False:
            await inter.delete_original_response()
            await inter.send(
                f'`{member.display_name}` does not want to marry you. {inter.author.mention} :pensive: :fist:'
            )
            self.currently_marrying = False

    @commands.slash_command(name='divorce')
    async def divorce(self, inter: disnake.AppCmdInter):
        """Divorce the person you're married with in case you're married with anybody."""

        if self.currently_divorcing is True:
            return await inter.send(
                'Uh oh.. it seems that there\'s already a divorce going on in the server! '
                'Wait for them to finish.',
                ephemeral=True
            )
        self.currently_divorcing = True

        data: Marriage = await self.bot.db.get('marriage', inter.author.id)

        if data is None or data.married_to == 0:
            self.currently_divorcing = False
            return await inter.send(f'{self.bot.denial} You are not married to anyone.', ephemeral=True)

        else:
            guild = self.bot.get_guild(1131710408542146602)
            usr = guild.get_member(data.married_to)

            view = utils.ConfirmViewInteraction(
                inter,
                new_message=f'{inter.author.mention} Did not react in time.'
            )
            await inter.send(f'Are you sure you want to divorce {usr.mention}?', view=view)
            await view.wait()
            if view.response is True:
                self.currently_divorcing = False
                mem: Marriage = await self.bot.db.get('marriage', usr.id)
                await self.bot.db.delete('marriages', {'_id': data.pk})
                await self.bot.db.delete('marriages', {'_id': mem.pk})

                e = f'You divorced {usr.mention} that you have been married ' \
                    f'since {utils.format_dt(data.married_since, "F")} ' \
                    f'(`{utils.human_timedelta(data.married_since)}`)'
                return await inter.edit_original_message(content=e, view=view)

            elif view.response is False:
                self.currently_divorcing = False
                e = f'You did not divorce {usr.mention}'
                return await inter.edit_original_message(content=e, view=view)

    @commands.slash_command(name='marriage')
    async def marriage(
        self,
        inter: disnake.AppCmdInter,
        member: disnake.Member = commands.Param(lambda inter: inter.author)
    ):
        """See who, the date and how much it's been since the member married their partner if they have one.

        Parameters
        ----------
        member: The member to view the marriage of.
        """

        data: Marriage = await self.bot.db.get('marriage', member.id)
        if data is None or data.married_to == 0:
            if member == inter.author:
                i = f'{self.bot.denial} You\'re not married to anyone.'
            else:
                i = f'{self.bot.denial} {member.mention} is not married to anyone.'
            return await inter.send(i, ephemeral=True)

        guild = self.bot.get_guild(1131710408542146602)
        mem = guild.get_member(data.married_to)
        em = disnake.Embed(title=f'Married to `{mem.display_name}`', colour=utils.blurple)
        if member == inter.author:
            i = 'You\'re married to'
        else:
            i = f'{member.mention} is married to'
        em.description = f'{i} {mem.mention} ' \
                         f'since {utils.format_dt(data.married_since, "F")} ' \
                         f'(`{utils.human_timedelta(data.married_since, accuracy=6)}`)'
        await inter.send(embed=em)

    @commands.slash_command(name='kiss')
    async def _kiss(self, inter: disnake.AppCmdInter, member: disnake.Member):
        """Kiss the person you are married with.

        Parameters
        ----------
        member: The member you want to kiss. (Must be the one you're married to.)
        """

        guild = self.bot.get_guild(1131710408542146602)
        data = await self.bot.db.get('marriage', inter.author.id)
        if inter.author.id != self.bot._owner_id:
            if data is None or data.married_to == 0:
                return await inter.send(
                    f'{self.bot.denial} You must be married to {member.mention} in order to kiss them.'
                )

        if inter.author.id != self.bot._owner_id:
            if member.id != data.married_to and data.married_to != 0:
                mem = guild.get_member(data.married_to)
                return await inter.send(
                    f'{self.bot.denial} You cannot kiss `{member.display_name}`!! '
                    f'You can only kiss {mem.mention}'
                )

        em = disnake.Embed(color=utils.red)
        em.set_image(url='https://cdn.discordapp.com/attachments/938411306762002456/938475662556151838/kiss.gif')
        await inter.send(
            f'{inter.author.mention} is giving you a hot kiss {member.mention} 🥺 💋',
            embed=em
        )

    @commands.slash_command(name='adopt')
    async def adopt(self, inter: disnake.AppCmdInter, member: disnake.Member):
        """Adopt someone into your family.

        Parameters
        ----------
        member: The member you want to adopt in your family.
        """

        if self.currently_adopting is True:
            return await inter.send(
                'Uh oh.. it seems like there\'s already an adoption going on in the server! '
                'Wait for them to finish.',
                ephemeral=True
            )
        self.currently_adopting = True

        if member.id == inter.author.id:
            self.currently_adopting = False
            return await inter.send(f'{self.bot.denial} You cannot adopt yourself.', ephemeral=True)
        elif member.bot and inter.author.id != self.bot._owner_id:
            self.currently_adopting = False
            return await inter.send(f'{self.bot.denial} You cannot adopt bots.', ephemeral=True)

        partner = False
        data1: Marriage = await self.bot.db.get('marriage', inter.author.id)

        if data1 and len(data1.adoptions) >= 7 and inter.author.id != self.bot._owner_id:
            self.currently_adopting = False
            return await inter.send(
                f'{self.bot.denial} You cannot adopt more than **7** people.',
                ephemeral=True
            )

        data2: Marriage = await self.bot.db.get('marriage', member.id)
        if data2 and inter.author.id in data2.adoptions:
            self.currently_adopting = False
            return await inter.send(
                f'{self.bot.denial} You cannot adopt the person that adopted you, what are you, dumb???',
                ephemeral=True
            )
        elif data1 and member.id in data1.adoptions:
            self.currently_adopting = False
            return await inter.send(
                f'{self.bot.denial} You already adopted that person.',
                ephemeral=True
            )
        else:
            adoptions = []
            for entry in await self.bot.db.find('marriage'):
                if member.id in entry.adoptions:
                    adoptions.append(entry)

        guild = self.bot.get_guild(1131710408542146602)
        if len(adoptions) == 1:
            self.currently_adopting = False
            mem = guild.get_member(adoptions[0].id)
            return await inter.send(
                f'{self.bot.denial} `{member.display_name}` is already adopted by {mem.mention}'
            )
        elif len(adoptions) == 2:
            self.currently_adopting = False
            mem1 = guild.get_member(adoptions[0].id)
            mem2 = guild.get_member(adoptions[1].id)
            return await inter.send(
                f'{self.bot.denial} `{member.display_name}` is already adopted by '
                f'{mem1.mention} and {mem2.mention}',
            )

        owner_entry = await self.bot.db.get('marriage')
        if owner_entry is not None:
            if owner_entry.married_to != 0:
                if member.id == owner_entry.married_to:
                    self.currently_adopting = False
                    return await inter.send(
                        f'{self.bot.denial} No. Only my master can own and be the daddy of {member.mention}'
                    )
                elif member.id == owner_entry.id:
                    self.currently_adopting = False
                    married_to = guild.get_member(owner_entry.married_to)
                    return await inter.send(
                        f'{self.bot.denial} No. Only {married_to.mention} can own and be the mommy of my master.'
                    )
        elif member.id == self.bot._owner_id:
            self.currently_adopting = False
            return await inter.send(f'{self.bot.denial} No.', ephemeral=True)

        if data1 and data1.married_to != 0:
            mem = guild.get_member(data1.married_to)
            view = utils.ConfirmViewInteraction(inter, react_user=mem)
            await inter.send(
                f'{mem.mention} your partner wants to adopt {member.mention}. Do you agree?',
                view=view
            )
            await view.wait()
            if view.response is False:
                self.currently_adopting = False
                return await inter.edit_original_message(
                    content=f'{inter.author.mention} It seems like your partner did not want to adopt {member.mention}.',
                    view=view
                )
            else:
                partner = True

        view = utils.ConfirmViewInteraction(inter, react_user=member)
        await inter.edit_original_message(
            f'{member.mention} do you wish to be part of **{inter.author.display_name}**\'s family?',
            view=view
        )
        await view.wait()
        if view.response is False:
            self.currently_adopting = False
            return await inter.edit_original_message(
                content=f'{inter.author.mention} It seems like {member.mention} does not want to be part of your family.',
                view=view
            )
        else:
            await inter.edit_original_message(
                content=f'{member.mention} You are now part of **{inter.author.display_name}**\'s family.',
                view=view
            )

        if partner is True:
            data2: Marriage = await self.bot.db.get('marriage', data1.married_to)
            data2.adoptions.append(member.id)
            await data2.commit()

        if data1 is None:
            await self.bot.db.add('marriages', Marriage(
                id=inter.author.id,
                married_to=0,
                married_since=utils.FIRST_JANUARY_1970,
                adoptions=[]
            ))
            data1 = await self.bot.db.get('marriage', inter.author.id)
        data1.adoptions.append(member.id)
        await data1.commit()

        await inter.send(f'You have adopted {member.mention} :heart: :tada:')
        self.currently_adopting = False

    @commands.slash_command(name='unadopt')
    async def unadopt(self, inter: disnake.AppCmdInter, member: disnake.Member):
        """Unadopt one of your children.

        Parameters
        ----------
        member: The member you want to unadopt.
        """

        if self.currently_unadopting is True:
            return await inter.send(
                'Uh oh.. looks like there\'s already an unadoption running in the server! '
                'Wait for them to finish.',
                ephemeral=True
            )
        self.currently_unadopting = True

        guild = self.bot.get_guild(1131710408542146602)
        data: Marriage = await self.bot.db.get('marriage', inter.author.id)
        if data is None or len(data.adoptions) == 0:
            self.currently_unadopting = False
            return await inter.send(f'You\'ve never adopted {member.mention}.')
        elif data.married_to != 0:
            mem = guild.get_member(data.married_to)
            data2: Marriage = await self.bot.db.get('marriage', data.married_to)
            view = utils.ConfirmViewInteraction(inter, react_user=mem)
            await inter.send(
                f'{mem.mention} your partner wants to unadopt {member.mention}. Do you agree?',
                view=view
            )
            await view.wait()
            if view.response is False:
                self.currently_unadopting = False
                return await inter.edit_original_message(
                    content=f'{inter.author.mention} It seems like your partner did not want to unadopt {member.mention}.',
                    view=None
                )
            else:
                await inter.edit_original_message(view=view)
                data2.adoptions.remove(member.id)
                await data2.commit()
        data.adoptions.remove(member.id)
        if len(data.adoptions) == 0 and data.married_to == 0:
            await self.bot.db.delete('marriages', {'_id': data.pk})
        else:
            await data.commit()

        await inter.send(f'You have unadopted {member.mention}')
        self.currently_unadopting = False

    @commands.slash_command(name='runaway')
    async def runaway(self, inter: disnake.AppCmdInter):
        """Run away from your family. That means you will "unadopt" yourself."""

        entries: Marriage = await self.bot.db.find('marriage')
        guild = self.bot.get_guild(1131710408542146602)
        if not entries:
            return await inter.send(f'{self.bot.denial} You are not adopted by anybody.', ephemeral=True)
        else:
            for entry in entries:
                entry: Marriage

                if inter.author.id not in entry.adoptions:
                    continue

                if entry.id == self.bot._owner_id or entry.married_to == self.bot._owner_id:
                    await guild.get_member(entry.id).send(
                        f'{inter.author.display_name}` Has tried to run away.'
                    )
                    return await inter.send(
                        'You cannot run away from my master. '
                        'He\'s been notified about your misbehaviour.',
                        ephemeral=True
                    )

                entry.adoptions.remove(inter.author.id)
                await entry.commit()
                await guild.get_member(entry.id).send(
                    f'`{inter.author.display_name}` Has run away from your family. '
                    'They are no longer adopted by you.'
                )
        await inter.send(
            'You have run away from your family. '
            'You are not adopted anymore and your ex-step-parents have been notified about this.'
        )

    @commands.slash_command(name='family')
    async def family(
        self,
        inter: disnake.AppCmdInter,
        member: disnake.Member = commands.Param(lambda inter: inter.author)
    ):
        """See your family members. This basically shows you who you have adopted, and who you are married to.

        Parameters
        ----------
        member: The member of who's family you want to see.
        """

        if member.bot:
            return await inter.send('Bots cannot have families.', ephemeral=True)

        em = disnake.Embed(color=utils.blurple)
        em.set_author(name=f'{member.display_name}\'s family', icon_url=member.display_avatar)
        data: Marriage = await self.bot.db.get('marriage', member.id)
        entries: Marriage = await self.bot.db.find('marriage')

        _adopted_by = []
        for entry in entries:
            if member.id in entry.adoptions:
                _adopted_by.append(entry)

        if data is None and len(_adopted_by) == 0:
            if member.id == inter.author.id:
                return await inter.send('You don\'t have a family :frowning:', ephemeral=True)
            else:
                return await inter.send(f'{member.mention} doesn\'t have a family :frowning:', ephemeral=True)

        guild = self.bot.get_guild(1131710408542146602)
        adopted_by = []
        for uid in _adopted_by:
            mem = guild.get_member(uid.id)
            if mem:
                adopted_by.append(mem.mention)
        adopted_by = ' and '.join(adopted_by) if len(adopted_by) != 0 else 'No one.'

        siblings = []
        if _adopted_by:
            entry = _adopted_by[0]
            for sibling in entry.adoptions:
                if sibling != member.id:
                    mem = guild.get_member(sibling)
                    siblings.append(f'{mem.mention} (`{mem.display_name}`)')

        siblings_count = len(siblings)
        siblings = '\n'.join(siblings) if len(siblings) != 0 else 'No siblings.'

        married_to = 'No partner.'
        adoptions = []
        if data is not None:
            if data.married_to != 0:
                mem = guild.get_member(data.married_to)
                married_since = utils.human_timedelta(data.married_since)
                married_to = f'{mem.mention} (married since `{married_since}`)'
            for adoption in data.adoptions:
                mem = guild.get_member(adoption)
                adoptions.append(f'{mem.mention} (`{mem.display_name}`)')
        adoptions_count = len(adoptions)
        adoptions = '\n'.join(adoptions) if len(adoptions) != 0 else 'No adoptions.'

        em.add_field('Married To', married_to, inline=False)
        em.add_field(f'Adoptions ({adoptions_count})', adoptions, inline=False)
        em.add_field('Adopted By', adopted_by, inline=False)
        em.add_field(f'Siblings ({siblings_count})', siblings, inline=False)
        em.set_footer(text=f'Requested by: {inter.author.display_name}')

        await inter.send(embed=em)

    @commands.Cog.listener()
    async def on_member_remove(self, member: disnake.Member):
        if member.guild.id != 1131710408542146602:
            return

        await self.bot.db.delete('marriage', {'_id': member.id})
        await self.bot.db.delete('marriage', {'married_to': member.id})

        for entry in await self.bot.db.find('marriage'):
            if member.id in entry.adoptions:
                entry.adoptions.remove(member.id)
                await entry.commit()


def setup(bot: Ukiyo):
    bot.add_cog(Marriages(bot))