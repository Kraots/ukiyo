from datetime import datetime

import disnake
from disnake.ext import commands

import utils
from utils import AFK

from main import Ukiyo


class AFKs(commands.Cog):
    def __init__(self, bot: Ukiyo):
        self.bot = bot

    @commands.slash_command(name='afk')
    async def afk(self, inter):
        pass

    @afk.sub_command(name='start')
    async def afk_start(self, inter: disnake.AppCmdInter, reason: str = None):
        """Start being afk. To stop just send any message.

        Parameters
        ----------
        reason: The reason you're afk.
        """

        data: AFK = await self.bot.db.get('afk', inter.author.id)
        if data is None:
            if reason is None:
                return await inter.send(
                    f'{self.bot.denial} You must give the reason or have a default afk set.',
                    ephemeral=True
                )

            await self.bot.db.add('afks', AFK(
                id=inter.author.id,
                reason=reason,
                date=datetime.utcnow(),
                is_afk=True
            ))

        elif data is not None:
            if data.is_afk is True:
                return await inter.send(
                    f'{self.bot.denial} You are already ``AFK``!',
                    ephemeral=True
                )
            reason = f'{reason} | {data.default}' if reason is not None else data.default
            reason = reason.replace('*', '')  # Make sure it doesn't mess with the default bolding of the reason.
            data.reason = reason
            data.date = datetime.utcnow()
            data.is_afk = True
            await data.commit()

        await inter.send(f'You are now ``AFK`` **->** **"{reason}"**')

    @afk.sub_command_group(name='default')
    async def afk_default(self, inter):
        pass

    @afk_default.sub_command(name='view')
    async def afk_default_view(self, inter: disnake.AppCmdInter):
        """View your default ``AFK`` reason, if you set any."""

        data: AFK = await self.bot.db.get('afk', inter.author.id)
        if data is None or data.default is None:
            return await inter.send(
                f'{self.bot.denial} You don\'t have a default ``AFK`` reason set!',
                ephemeral=True
            )

        await inter.send(f'Your default ``AFK`` reason is: **"{data.default}"**')

    @afk_default.sub_command(name='set')
    async def afk_default_set(self, inter: disnake.AppCmdInter, default: str):
        """Sets your default ``AFK`` reason.

        Parameters
        ----------
        default: The default reason you want to set.
        """

        data: AFK = await self.bot.db.get('afk', inter.author.id)
        default = default.replace('*', '')  # Make sure it doesn't mess with the default bolding of the reason.
        if data is None:
            await self.bot.db.add('afks', AFK(
                id=inter.author.id,
                default=default
            ))
        else:
            data.default = default
            await data.commit()

        await inter.send(f'Successfully set your default ``AFK`` reason to: **"{default}"**')

    @afk_default.sub_command(name='remove')
    async def afk_default_remove(self, inter: disnake.AppCmdInter):
        """Removes your default ``AFK`` reason."""

        data: AFK = await self.bot.db.get('afk', inter.author.id)
        if data is None:
            return await inter.send(
                f'{self.bot.denial} You don\'t have a default ``AFK`` reason set!',
                ephemeral=True
            )
        await self.bot.db.delete('afk', {'_id': data.pk})

        await inter.send('Successfully removed your default ``AFK`` reason.')

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.author.bot:
            return

        data: AFK = await self.bot.db.get('afk', message.author.id)
        if data is not None:
            if data.is_afk is True:
                m = await message.reply(
                    'Welcome back! Removed your ``AFK``\nYou have been ``AFK`` '
                    f'since {utils.format_dt(data.date, "F")} '
                    f'(`{utils.human_timedelta(dt=data.date, accuracy=6)}`)'
                )
                if data.default is None:
                    await self.bot.db.delete('afk', {'_id': data.pk})
                else:
                    data.is_afk = False
                    data.reason = None
                    data.date = None
                    await data.commit()
                return await utils.try_delete(m, delay=30.0)

        for user in message.mentions:
            data: AFK = await self.bot.db.get('afk', user.id)
            if data is not None and data.is_afk is True:
                m = await message.reply(
                    f'**{user.display_name}** is ``AFK`` **->** **"{data.reason}"** '
                    f'*since {utils.format_dt(data.date, "F")} '
                    f'(`{utils.human_timedelta(dt=data.date, accuracy=6)}`)*')
                await utils.try_delete(m, delay=30.0)

    @commands.Cog.listener()
    async def on_member_remove(self, member: disnake.Member):
        if member.guild.id != 1131710408542146602:
            return

        await self.bot.db.delete('afks', {'_id': member.id})


def setup(bot: Ukiyo):
    bot.add_cog(AFKs(bot))