import os

from aiohttp import ClientSession
from traceback import format_exception

import disnake
from disnake.ext import commands

import utils
from .constants import Channels

__all__ = ('Context',)


class Context(commands.Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def session(self) -> ClientSession:
        return self.bot.session

    @property
    def agree(self) -> disnake.PartialEmoji:
        return disnake.PartialEmoji(name='agree', id=938412195627290684)

    @property
    def disagree(self) -> disnake.PartialEmoji:
        return disnake.PartialEmoji(name='disagree', id=938412196663271514)

    @property
    def thumb(self) -> disnake.PartialEmoji:
        return disnake.PartialEmoji(name='thumb', id=938412204926062602)

    @property
    def denial(self) -> str:
        return f'>>> {self.disagree}'

    @property
    def ukiyo(self) -> disnake.Guild:
        return self.bot.get_guild(1131710408542146602)

    @disnake.utils.cached_property
    def replied_reference(self) -> disnake.MessageReference | None:
        ref = self.message.reference
        if ref and isinstance(ref.resolved, disnake.Message):
            return ref.resolved.to_reference()
        return None

    async def trigger_typing(self) -> None:
        try:
            channel = await self._get_channel()
            await self._state.http.send_typing(channel.id)
        except disnake.Forbidden:
            pass

    async def better_reply(self, *args, **kwargs) -> disnake.Message:
        if self.replied_reference is not None:
            try:
                del kwargs['reference']
            except KeyError:
                pass
            return await self.send(*args, reference=self.replied_reference, **kwargs)
        else:
            return await super().reply(*args, **kwargs)

    async def reraise(self, error):
        if isinstance(error, commands.NotOwner):
            await self.reply(f'{self.denial} You do not own this bot, this is an owner only command.', delete_after=8)
            await utils.try_delete(self.message, delay=8)
            return

        elif isinstance(error, commands.CommandOnCooldown):
            if error.retry_after > 60.0:
                time = utils.time_phaser(error.retry_after)
            else:
                time = f'{error.retry_after:.2f} seconds'
            return await self.reply(
                f'{self.denial} You are on cooldown, **`{time}`** remaining.'
            )

        elif isinstance(error, commands.DisabledCommand):
            self.command.reset_cooldown(self)
            return await self.reply('This command is currently disabled!')

        elif isinstance(error, commands.MaxConcurrencyReached):
            await utils.try_delete(self.message, delay=5.0)
            await self.reply(
                'You are already using this command! Please wait until you complete it first.',
                delete_after=5.0
            )
            return

        elif isinstance(error, commands.errors.MissingRequiredArgument):
            _missing_args = list(self.command.clean_params)
            missing_args = [f'`{arg}`' for arg in _missing_args[_missing_args.index(error.param.name):]]
            return await self.reply(
                f"{self.denial} You are missing the following required arguments for this command:\n "
                f"\u2800\u2800{utils.human_join(missing_args, final='and')}\n\n"
                "If you don't know how to use this command, please type "
                f"`!help {self.command.qualified_name}` for more information on how to use it and what each "
                "argument means."
            )

        elif isinstance(error, commands.errors.MemberNotFound):
            await self.reply(f"{self.denial} Could not find member.")
            self.command.reset_cooldown(self)
            return

        elif isinstance(error, commands.errors.UserNotFound):
            await self.reply(f"{self.denial} Could not find user.")
            self.command.reset_cooldown(self)
            return

        elif isinstance(error, commands.errors.CheckFailure):
            self.command.reset_cooldown(self)
            return

        elif isinstance(error, commands.ExpectedClosingQuoteError):
            self.command.reset_cooldown(self)
            return await self.reply(f'Expected closing `{error.close_quote}`')

        elif isinstance(error, commands.InvalidEndOfQuotedStringError):
            self.command.reset_cooldown(self)
            return await self.reply(f'Expected space after ending the quote, not `{error.char}`')

        elif (
            isinstance(error, commands.TooManyArguments) or
            isinstance(error, commands.BadArgument) or
            isinstance(error, commands.CommandNotFound)
        ):
            return

        elif (
            isinstance(error, commands.CommandInvokeError) and
            isinstance(error.original, utils.Canceled)
        ):
            return await self.reply('Canceled.')

        else:
            get_error = "".join(format_exception(error, error, error.__traceback__))
            em = disnake.Embed(description=f'```py\n{get_error}\n```')
            await self.bot._owner.send(
                content=f"**An error occurred with the command `{self.command}`, "
                        "here is the error:**",
                embed=em
            )
            await self.reply(f'{self.denial} An error occurred')