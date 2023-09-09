import random
from datetime import datetime

import disnake
from disnake.ext import commands, tasks

import utils

from main import Ukiyo


class JoinGiveawayButton(disnake.ui.Button):
    def __init__(self, label: str = '0'):
        super().__init__(
            label=f'{label} participants',
            custom_id='ukiyo:giveaways:join_btn',
            style=disnake.ButtonStyle.blurple,
            emoji='🎉'
        )

    async def callback(self, inter: disnake.MessageInteraction):
        giveaway: utils.Giveaway = await inter.bot.db.get('giveaways', inter.message.id)
        if inter.author.id in giveaway.participants:
            return await inter.send(
                'You are already participating in this giveaway!',
                ephemeral=True
            )

        entry: utils.Level = await inter.bot.db.get('levels', inter.author.id)
        if entry is None:
            return await inter.send(
                'You have never sent a message in the server. Cannot participate!',
                ephemeral=True
            )
        elif entry.messages_count < giveaway.messages_requirement:
            needed_messages = giveaway.messages_requirement - entry.messages_count
            return await inter.send(
                'Sorry! You don\'t seem to meet this giveaway\'s message requirement.\n'
                f'You need **{needed_messages:,}** more messages if you want to participate.\n\n'
                '**NOTE:** If you spam, your message count will be reset by one of our staff members, '
                'so please refrain from spamming.',
                ephemeral=True
            )

        giveaway.participants.append(inter.author.id)
        await giveaway.commit()

        self.label = f'{len(giveaway.participants)} participants'
        view = self.view
        self.view.children[0] = self
        await inter.message.edit(view=view)

        await inter.send('You are now participating in this giveaway.', ephemeral=True)


class GiveAwayCreationView(disnake.ui.View):
    def __init__(self, bot: Ukiyo, author: disnake.Member):
        super().__init__()
        self.bot = bot
        self.author = author

        self.prize = None
        self.message_req = 0
        self.expire_date = None
        self.ping_everyone = False

    async def on_error(self, error: Exception, item, interaction: disnake.MessageInteraction) -> None:
        if isinstance(error, TimeoutError):
            if interaction.response.is_done():
                method = interaction.edit_original_message
            else:
                method = interaction.response.edit_message
            await method(content='You took too long. Goodbye.', view=None, embed=None)
            return self.stop()
        await self.bot.inter_reraise(interaction, item, error)

    async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
        if inter.author.id not in (self.bot._owner_id, self.author.id):
            await inter.send(
                f'Only `{self.author}` can use the buttons on this message.',
                ephemeral=True
            )
            return False
        return True

    def lock_all(self):
        for child in self.children:
            if child.label == 'Abort':
                continue
            child.disabled = True

    def unlock_all(self):
        for child in self.children:
            if child.label == 'Confirm':
                if self.prize is not None:
                    child.disabled = False
                else:
                    child.disabled = True
            else:
                child.disabled = False

    async def prepare_embed(self):
        if self.expire_date is not None:
            _duration = (await utils.UserFriendlyTime().convert(self.expire_date)).dt
            duration = utils.human_timedelta(_duration, suffix=False, accuracy=4)
        else:
            duration = 'Not set.'

        em = disnake.Embed(title='Giveaway Creation', color=utils.blurple)
        em.add_field(name='Prize', value=self.prize, inline=False)
        em.add_field(name='Duration', value=duration, inline=False)
        em.add_field(name='Message Requirements', value=f'{self.message_req:,}', inline=False)

        return em

    @disnake.ui.button(label='Prize', style=disnake.ButtonStyle.blurple)
    async def set_prize(self, button: disnake.Button, inter: disnake.MessageInteraction):
        self.lock_all()
        msg_content = 'Cool, let\'s set the prize. Send the giveaway\'s prize in the next message...'

        await inter.response.edit_message(content=msg_content, view=self)
        msg = await self.bot.wait_for(
            'message',
            timeout=300.0,
            check=lambda m: m.author.id == inter.author.id and m.channel.id == inter.channel.id
        )
        if self.is_finished():
            return

        if msg.content:
            clean_content = await utils.clean_inter_content()(inter, msg.content)
        else:
            clean_content = msg.content

        if msg.attachments:
            clean_content += f'\n{msg.attachments[0].url}'

        c = None
        if len(clean_content) > 1024:
            c = 'Prize cannot be longer than **1024** characters...'
        else:
            self.prize = clean_content

        self.unlock_all()
        await inter.edit_original_message(content=c, embed=(await self.prepare_embed()), view=self)

    @disnake.ui.button(label='Duration', style=disnake.ButtonStyle.blurple)
    async def set_duration(self, button: disnake.Button, inter: disnake.MessageInteraction):
        self.lock_all()
        msg_content = 'Cool, let\'s set the duration. Send how long you wish the givaway to last for in the next message...'

        await inter.response.edit_message(content=msg_content, view=self)
        msg = await self.bot.wait_for(
            'message',
            timeout=300.0,
            check=lambda m: m.author.id == inter.author.id and m.channel.id == inter.channel.id
        )
        if self.is_finished():
            return

        c = None
        content = msg.content
        content = content + ' - '
        try:
            await utils.UserFriendlyTime().convert(content + ' -')
        except commands.BadArgument as e:
            c = f'{self.bot.denial} {e}'
        self.expire_date = content

        self.unlock_all()
        await inter.edit_original_message(content=c, embed=(await self.prepare_embed()), view=self)

    @disnake.ui.button(label='Messages Requirement', style=disnake.ButtonStyle.blurple)
    async def set_message_req(self, button: disnake.Button, inter: disnake.MessageInteraction):
        self.lock_all()
        msg_content = 'Cool, let\'s set the messages requirement. Send the giveaway\'s message requirement in the next message...'

        await inter.response.edit_message(content=msg_content, view=self)
        msg = await self.bot.wait_for(
            'message',
            timeout=300.0,
            check=lambda m: m.author.id == inter.author.id and m.channel.id == inter.channel.id
        )
        if self.is_finished():
            return

        if msg.content:
            clean_content = await utils.clean_inter_content()(inter, msg.content)
        else:
            clean_content = msg.content

        clean_content = utils.format_amount(clean_content)

        c = None
        if clean_content is None:
            c = 'Message requirement cannot be empty.'
        else:
            try:
                clean_content = int(clean_content)
            except ValueError:
                c = 'Message requirement must be a number only!'
            else:
                self.message_req = clean_content

        self.unlock_all()
        await inter.edit_original_message(content=c, embed=(await self.prepare_embed()), view=self)

    @disnake.ui.button(label='@everyone OFF')
    async def set_everyone_ping(self, button: disnake.Button, inter: disnake.MessageInteraction):
        if self.ping_everyone is False:
            self.ping_everyone = True
            button.label = '@everyone ON'
        else:
            self.ping_everyone = False
            button.label = '@everyone OFF'
        await inter.response.edit_message(view=self)

    @disnake.ui.button(label='Confirm', style=disnake.ButtonStyle.green, row=1)
    async def confirm(self, button: disnake.Button, inter: disnake.MessageInteraction):
        if self.prize is None:
            return await inter.response.edit_message(content='You didn\'t set the prize!')
        elif self.expire_date is None:
            return await inter.response.edit_message(content='You didn\'t set the duration!')
        await inter.response.edit_message(view=None)

        expiry_date = (await utils.UserFriendlyTime().convert(self.expire_date)).dt

        guild = self.bot.get_guild(1131710408542146602)
        news_channel = guild.get_channel(utils.Channels.news)
        em = disnake.Embed(
            colour=utils.green,
            title='🎁 New Giveaway',
            description='Press the button below that contains the 🎉 to participate.'
        )
        em.add_field(
            'Prize',
            self.prize,
            inline=False
        )
        em.add_field(
            'Expires At',
            f'{utils.format_dt(expiry_date, "F")} ({utils.format_relative(expiry_date)})',
            inline=False
        )
        em.add_field(
            'Message Requirement',
            f'You need a total of **{self.message_req:,}** messages in order to participate to this giveaway.',
            inline=False
        )

        em.set_footer(text=f'Giveaway by: {inter.author.display_name}')
        if self.ping_everyone is False:
            allowed_mentions = disnake.AllowedMentions(everyone=False)
            content = None
        else:
            allowed_mentions = disnake.AllowedMentions(everyone=True)
            content = '@everyone'

        view = disnake.ui.View(timeout=None)
        view.add_item(JoinGiveawayButton())

        msg: disnake.Message = await news_channel.send(
            content=content,
            embed=em,
            allowed_mentions=allowed_mentions,
            view=view
        )
        await msg.pin(reason='New Giveaway.')
        await news_channel.purge(limit=1)
        await self.bot.db.add('giveaways', utils.Giveaway(
            id=msg.id,
            prize=self.prize,
            expire_date=expiry_date,
            messages_requirement=self.message_req
        ))

        v = disnake.ui.View()
        v.add_item(disnake.ui.Button(label='Jump!', url=msg.jump_url))
        await inter.message.reply('Giveaway sent.', view=v)

        self.stop()

    @disnake.ui.button(label='Abort', style=disnake.ButtonStyle.red, row=1)
    async def cancel(self, button: disnake.Button, inter: disnake.MessageInteraction):
        await inter.response.edit_message(
            content='Giveaway aborted.',
            view=None,
            embed=None
        )
        self.stop()


class Giveaways(commands.Cog):
    def __init__(self, bot: Ukiyo):
        self.bot = bot

        self.check_giveaway.start()

    async def end_giveaway(self, gw: utils.Giveaway):
        guild = self.bot.get_guild(1131710408542146602)
        participants = gw.participants + [0]
        for i in range(5):
            random.shuffle(participants)

        # We do this so that if the member has left
        # it'll keep rerolling until it picks a
        # winner that's still in the server.
        while True:
            winner_id = random.choice(participants)
            winner = guild.get_member(winner_id)
            if winner is None:
                participants.pop(participants.index(winner_id))
                if len(participants) == 0:
                    winner = 'No One.'
                    break
            else:
                winner = f'{winner.mention} (`{winner.display_name}`)'
                break

        channel = guild.get_channel(utils.Channels.news)

        try:
            msg = await channel.fetch_message(gw.id)
        except disnake.NotFound:
            return await self.bot.db.delete('giveaways', {'_id': gw.pk})

        em = msg.embeds[0]
        em.color = utils.red
        em.title = '🎁 Giveaway Ended'
        em.add_field('Winner', winner, inline=False)

        v = disnake.ui.View()
        btn = disnake.ui.ActionRow.rows_from_message(msg)[0].children[0]
        btn.disabled = True
        v.add_item(btn)
        await msg.edit(embed=em, view=v)
        await msg.unpin(reason='Giveaway Ended.')

        fmt = '**⚠️ Giveaway Ended ⚠️**'
        if winner != 'No One.':
            fmt += f'\nCongratulations {winner}, you won **{gw.prize}**'
        else:
            fmt += '\nIt appears that no one that participated was still in the server. No winner.'
        await msg.reply(fmt)
        await self.bot.db.delete('giveaways', {'_id': gw.pk})

    @commands.slash_command(name='giveaway')
    async def giveaway(self, inter):
        pass

    @giveaway.sub_command(name='create')
    async def giveaway_create(self, inter: disnake.AppCmdInter):
        """Create a new giveaway."""

        if not any(r for r in (utils.StaffRoles.owner, utils.StaffRoles.admin) if r in (role.id for role in inter.author.roles)):
            if inter.author.id != self.bot._owner_id:
                await inter.send(
                    f'{self.bot.denial} This command can only be used by staff members!',
                    ephemeral=True
            )

        view = GiveAwayCreationView(self.bot, inter.author)
        await inter.send(embed=(await view.prepare_embed()), view=view)

    @giveaway.sub_command(name='end')
    async def giveaway_end(
        self,
        inter: disnake.AppCmdInter,
        giveaway_id: int = commands.Param(large=True)
    ):
        """End the giveaway earlier than the expiration date set.
        
        Parameters
        ----------
        giveaway_id: The message id of the giveaway you want to cancel.
        """

        if not any(r for r in (utils.StaffRoles.owner, utils.StaffRoles.admin) if r in (role.id for role in inter.author.roles)):
            if inter.author.id != self.bot._owner_id:
                await inter.send(
                    f'{self.bot.denial} This command can only be used by staff members!',
                    ephemeral=True
            )

        await inter.response.defer()

        giveaway: utils.Giveaway = await self.bot.db.get('giveaway', giveaway_id)
        if giveaway is None:
            return await inter.send(
                f'{self.bot.denial} No giveaway with that id found.',
                ephemeral=True
            )

        await self.end_giveaway(giveaway)
        await inter.send('Giveaway ended.', ephemeral=True)

    @commands.Cog.listener()
    async def on_ready(self):
        for gw in await self.bot.db.find('giveaways'):
            view = disnake.ui.View(timeout=None)
            view.add_item(JoinGiveawayButton(str(len(gw.participants))))
            self.bot.add_view(view, message_id=gw.id)

    @tasks.loop(seconds=5.0)
    async def check_giveaway(self):
        giveaways: list[utils.Giveaway] = await self.bot.db.find_sorted('giveaways', 'expire_date', 1)
        now = datetime.utcnow()
        for gw in giveaways[:10]:
            if gw.expire_date <= now:
                await self.end_giveaway(gw)

    @check_giveaway.before_loop
    async def wait_until_ready_(self):
        await self.bot.wait_until_ready()


def setup(bot: Ukiyo):
    bot.add_cog(Giveaways(bot))