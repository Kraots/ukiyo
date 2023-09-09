from dotenv import load_dotenv
load_dotenv()

import os
from typing import Optional
from datetime import datetime
from collections import Counter
from traceback import format_exception

import mafic

from dulwich.repo import Repo

import disnake
from disnake.ext import commands

import utils
from utils.views.help_command import PaginatedHelpCommand

TOKEN = os.getenv('BOT_TOKEN')


class Ukiyo(commands.Bot):
    def __init__(self):
        super().__init__(
            help_command=PaginatedHelpCommand(),
            command_prefix=('!', '?'),
            case_insensitive=True,
            test_guilds=[1131710408542146602],
            strip_after_prefix=True,
            allowed_mentions=disnake.AllowedMentions(
                roles=False, everyone=False, users=True
            ),
            intents=disnake.Intents.all(),
            max_messages=100000
        )

        r = Repo('.')
        self.git_hash = r.head().decode('utf-8')
        r.close()

        self._owner_id = 1114756730157547622

        self.db: utils.databases.Database = utils.databases.Database()

        self.socket_events = Counter()
        self.execs = {}

        self.bad_words = {}
        self.loop.create_task(self.add_bad_words())

        self.webhooks = {}

        self.pool = mafic.NodePool(self)
        self.loop.create_task(self.add_nodes())

        self.added_views = False

        self.load_extension('jishaku')
        os.environ['JISHAKU_NO_DM_TRACEBACK'] = '1'
        os.environ['JISHAKU_FORCE_PAGINATOR'] = '1'
        os.environ['JISHAKU_EMBEDDED_JSK'] = '1'
        os.environ['JISHAKU_EMBEDDED_JSK_COLOR'] = 'blurple'

        self.load_extension('reload_cogs')

        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                self.load_extension(f'cogs.{filename[:-3]}')

    async def on_ready(self):
        if not hasattr(self, 'uptime'):
            self.uptime = datetime.utcnow()
            await self.db.add_to_cache()

        data: utils.Misc = await utils.Misc.get()
        if data is None:
            data = await utils.Misc().commit()
        for cmd_name in data.disabled_commands:
            cmd = self.get_command(cmd_name)
            if cmd is None:
                data.disabled_commands.remove(cmd_name)
                await data.commit()
            else:
                cmd.enabled = False

        if len(self.webhooks) == 0:
            av = self.user.display_avatar
            logs = await self.get_webhook(
                self.get_channel(utils.Channels.logs),
                avatar=av
            )
            mod_logs = await self.get_webhook(
                self.get_channel(utils.Channels.moderation_logs),
                avatar=av
            )
            message_logs = await self.get_webhook(
                self.get_channel(utils.Channels.messages_logs),
                avatar=av
            )
            welcome_webhook = await self.get_webhook(
                self.get_channel(utils.Channels.welcome),
                avatar=av
            )
            self.webhooks['logs'] = logs
            self.webhooks['mod_logs'] = mod_logs
            self.webhooks['message_logs'] = message_logs
            self.webhooks['welcome_webhook'] = welcome_webhook

        if self.added_views is False:
            self.add_view(utils.ColoursButtonRoles(), message_id=1150152735665180703)
            self.add_view(utils.ColoursButtonRoles(), message_id=1150152737259016273)
            self.add_view(utils.ColoursButtonRoles(), message_id=1150152739423256637)
            self.add_view(utils.ColoursButtonRoles(), message_id=1150152742136975370)
            self.add_view(utils.ColoursButtonRoles(), message_id=1150152744104108133)

            self.add_view(utils.GenderButtonRoles(), message_id=1150152509596389436)
            self.add_view(utils.PronounsButtonRoles(), message_id=1150152553649160273)
            self.add_view(utils.SexualityButtonRoles(), message_id=1150152604710617108)
            self.add_view(utils.AgeButtonRoles(), message_id=1150152655126151308)
            self.add_view(utils.DMSButtonRoles(), message_id=1150152694061862992)

        if not hasattr(self, '_presence_changed'):
            activity = disnake.Activity(type=disnake.ActivityType.watching, name='you')
            await self.change_presence(status=disnake.Status.dnd, activity=activity)
            self._presence_changed = True

        await self.collection_cleanup(utils.Intros)
        await self.collection_cleanup(utils.Level)
        await self.collection_cleanup(utils.AFK)
        await self.collection_cleanup(utils.Birthday)

        print('Bot is online!')

    @property
    def _owner(self) -> disnake.User:
        # Only returns my user.
        if self._owner_id:
            return self.get_user(self._owner_id)

    async def process_commands(self, message):
        ctx = await self.get_context(message)
        await self.invoke(ctx)

    async def get_context(self, message, *, cls=utils.Context):
        return await super().get_context(message, cls=cls)

    async def get_webhook(
        self,
        channel: disnake.TextChannel,
        *,
        name: str = "ukiyo",
        avatar: disnake.Asset = None,
    ) -> disnake.Webhook:
        """Returns the general bot hook or creates one."""

        webhooks = await channel.webhooks()
        webhook = disnake.utils.find(lambda w: w.name and w.name.lower() == name.lower(), webhooks)

        if webhook is None:
            webhook = await channel.create_webhook(
                name=name,
                avatar=await avatar.read() if avatar else None,
                reason="Used ``get_webhook`` but webhook didn't exist",
            )

        return webhook

    async def reference_to_message(
        self, reference: disnake.MessageReference
    ) -> Optional[disnake.Message]:
        if reference._state is None or reference.message_id is None:
            return None

        channel = reference._state.get_channel(reference.channel_id)
        if channel is None:
            return None

        if not isinstance(channel, (disnake.TextChannel, disnake.Thread)):
            return None

        try:
            return await channel.fetch_message(reference.message_id)
        except disnake.NotFound:
            return None
        
    async def inter_reraise(self, inter, item: disnake.ui.Item, error):
        if isinstance(error, utils.Canceled):
            if inter.response.is_done():
                await inter.followup.send('Canceled.', ephemeral=True)
                return await inter.author.send('Canceled.')
            else:
                await inter.response.send_message('Canceled.', ephemeral=True)
                return await inter.author.send('Canceled.')
        disagree = '<:disagree:938412196663271514>'
        get_error = "".join(format_exception(error, error, error.__traceback__))
        em = disnake.Embed(description=f'```py\n{get_error}\n```')
        await self._owner.send(
            content="**An error occurred with a view for the user "
                    f"`{inter.author}` (**{inter.author.id}**), "
                    "here is the error:**\n"
                    f"`View:` **{item.view.__class__}**\n"
                    f"`Item Type:` **{item.type}**\n"
                    f"`Item Row:` **{item.row or '0'}**",
            embed=em
        )
        fmt = f'> {disagree} An error occurred'
        if inter.response.is_done():
            await inter.followup.send(fmt, ephemeral=True)
        else:
            await inter.response.send_message(fmt, ephemeral=True)

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

    async def add_bad_words(self):
        data: utils.Misc = await utils.Misc.get()
        if data and data.bad_words:
            for word, added_by in data.bad_words.items():
                self.bad_words[word] = added_by

    async def add_nodes(self):
        await self.pool.create_node(
            host='127.0.0.1',
            port=2333,
            label='MAIN',
            password='youshallnotpass'
        )

    async def collection_cleanup(self, collection) -> None:
        """Searches and deletes every single document that is related to a user that isn't in ukiyo anymore.

        Parameters
        ----------
            collection: :class:`.AsyncIOMotorCollection`
                The collection object from which to delete.

        Return
        ------
            `None`
        """

        guild = self.get_guild(1131710408542146602)
        async for entry in collection.find():
            if entry.id not in [m.id for m in guild.members]:
                await entry.delete()


Ukiyo().run(TOKEN)