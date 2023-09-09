from typing import List, NamedTuple
import asyncio
import random

from datetime import datetime
from dateutil.relativedelta import relativedelta

import disnake
from disnake.ext import commands, tasks

import utils
from utils import Context

import mafic

from main import Ukiyo


class AudioData(NamedTuple):
    track: mafic.Track
    user: disnake.Member


class Queue:
    """
    A class to queue songs.

    This is rather highly unneeded since I can just make a list or
    a list of dicts for more info, but i find it rather convenient
    to just have it as a class.
    """

    def __init__(self):
        self._queue: List[AudioData] = []
        self._loop: bool = False
        self.looped_song: mafic.Track | None = None

        self.shuffled: bool = False

    @property
    def queue(self) -> List[AudioData]:
        return self._queue

    def add_track(self, track: mafic.Track, user: disnake.Member):
        """
        Adds a track to the queue.

        Parameters
        ----------
            track: :class:`mafic.Track`
                The track to add to the queue.

            user: :class:`disnake.Member`
                The member that added this track.

        Return
        ------
            `None`
        """

        self._queue.append(AudioData(track, user))

    def remove_track(self, index: int = None) -> bool:
        """
        Remove a track from the queue.

        Parameters
        ----------
            index: :class:`int`
                The index of the song to remove.

        Return
        ------
            :class:`bool`
                `True` if the track was removed successfully and `False`
                if the there was an :class:`IndexError`.
        """

        if not self.queue:
            return False
        elif index > len(self.queue):
            return False
        elif index < 0:
            return False
        else:
            self._queue.pop(index)
            return True

    def get_audio_data(self, index: int) -> AudioData | None:
        """
        Get the audio data from the specified index.

        Parameters
        ----------
            index: :class:`int`
                The index from which to take the audio data from.

        Return
        ------
            :class:`AudioData` | None
        """

        try:
            return self._queue[index]
        except IndexError:
            return None

    def get_latest_track(self) -> mafic.Track | None:
        """Gets the latest track."""

        return self.get_audio_data(0).track if self.get_audio_data(0) is not None else None

    def loop(self):
        """Starts looping the current playlist."""

        self._loop = True

    def unloop(self):
        """Stops looping the current playlist."""

        self._loop = False

    def is_looping(self) -> bool:
        """
        Returns whether the queue is currently looped or not.

        Return
        ------
            :class:`bool`
        """

        return self._loop

    def clear(self):
        """Clears the queue and removes the looped song."""

        self._queue = []
        self.looped_song = None

    def reset(self):
        """Resets the queue's data."""

        self._queue = []
        self._loop = False
        self.looped_song = None
        self.shuffled = False

    def shuffle(self):
        """Shuffles the queue."""

        self.shuffled = True
        for _ in range(5):
            random.shuffle(self._queue)


class Music(commands.Cog):
    def __init__(self, bot: Ukiyo):
        self.bot = bot

        self.dj: disnake.Member = None
        self.is_paused: bool = False
        self.queue: Queue = Queue()
        self.vol: int = 10

        self.invoked_ids = []
        self.invoked_ids_check.start()

    async def cog_check(self, ctx: Context):
        if ctx.author.id != self.bot._owner_id:
            if ctx.channel.id not in (
                utils.Channels.music_commands, utils.Channels.no_mic_chat,
            ):
                raise commands.CheckFailure('Not proper channel.')
        return True

    @property
    def display_emoji(self) -> str:
        return '🎵'

    @tasks.loop(seconds=18000)  # Every 6 hours.
    async def invoked_ids_check(self):
        self.invoked_ids = []

    # Instead of adding this only to the `play` command,
    # we add it to every single one 'just in case' it's
    # not only happening to the `play` command, although
    # that hasn't even happened before, but better be safe
    # than sorry.
    async def cog_before_invoke(self, ctx: Context):
        if ctx.message.id in self.invoked_ids:
            raise commands.CheckFailure('Command invoked twice from the same message')
        else:
            self.invoked_ids.append(ctx.message.id)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: disnake.Member,
        before: disnake.VoiceState,
        after: disnake.VoiceState
    ):
        if (
            (member.guild.id != 1131710408542146602) or
            (before.channel is None) or
            (member.bot is True) or
            (member.guild.voice_client is None)
        ):
            return

        elif before.channel.id == member.guild.voice_client.channel.id:
            if len(before.channel.members) == 1:
                self.queue.reset()
                self.is_paused = False
                self.dj = None
                self.vol = 10
                await member.guild.voice_client.destroy()
            else:
                if self.dj == member:
                    self.dj = None

    @commands.Cog.listener('on_track_end')
    async def on_track_end(self, event: mafic.TrackEndEvent):
        if self.queue.looped_song:
            return await event.player.play(event.track, volume=self.vol)

        if self.queue.shuffled:
            self.queue.shuffled = False
            track = self.queue.get_latest_track()
            if self.is_paused is False:
                await event.player.play(track, volume=self.vol)
        else:
            audio_data = self.queue.get_audio_data(0)
            self.queue.remove_track(0)

            if self.queue.is_looping():
                self.queue.add_track(*audio_data)

            if self.queue.queue:
                track = self.queue.get_latest_track()
                if self.is_paused is False:
                    await event.player.play(track, volume=self.vol)
            else:
                self.is_paused = False
                self.dj = None
                self.queue.reset()
                self.vol = 10
                await event.player.destroy()

    @staticmethod
    async def get_player(ctx: Context) -> mafic.Player:
        if not ctx.guild.voice_client:
            player = await ctx.author.voice.channel.connect(cls=mafic.Player)
        else:
            player = ctx.guild.voice_client

        return player

    async def check_dj(self, ctx: Context):
        if ctx.author.id != self.bot._owner_id:
            if self.dj is not None:
                if ctx.author != self.dj:
                    if not any([True for r in ctx.author.roles if r.id in (
                        utils.StaffRoles.owner, utils.StaffRoles.admin
                    )]):
                        await ctx.reply('Cannot perform that command since you are not the dj.')
                        raise commands.CheckFailure('User is not the dj.')

    @staticmethod
    def format_time(seconds: int | float) -> str:
        """Formats the time from seconds to h:m:s"""

        s, m, h = (0, 0, 0)
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)

        formated_time = []
        if h > 0:
            formated_time.append(str(int(round(h, 0))))
        if m > 0:
            formated_time.append(str(int(round(m, 0))))
        else:
            if h > 0:
                formated_time.append('00')
            else:
                formated_time.append('0')
        if s > 0:
            s = str(int(round(s, 0)))
            if len(s) == 1:
                s = '0' + s
            formated_time.append(s)
        else:
            formated_time.append('00')

        return ':'.join(formated_time)

    @commands.command(name='volume', aliases=('vol',))
    async def set_volume(self, ctx: Context, volume: int = 10):
        """Set the volume for the player.

        `volume` **->** The volume to set.
        """

        await self.check_dj(ctx)

        if ctx.author.id != self.bot._owner_id:
            if volume > 50:
                return await ctx.reply(f'{ctx.denial} The volume is too high')

        if volume > 30:  # anything above 30.
            fmt = f'> 🔊 Volume successfully set to **{volume}.**'
        elif volume in range(15, 31):  # between 15 and 30.
            fmt = f'> 🔉 Volume successfully set to **{volume}.**'
        else:
            fmt = f'> 🔈 Volume successfully set to **{volume}.**'

        player: mafic.Player = await self.get_player(ctx)
        await player.set_volume(volume)
        self.vol = volume

        await ctx.reply(fmt)

    @commands.command(name='shuffle', aliases=('sh',))
    async def shuffle_queue(self, ctx: Context):
        """Shuffles the queue."""

        await self.check_dj(ctx)
        self.queue.shuffle()

        player = await self.get_player(ctx)
        await player.stop()

        await ctx.reply('> 🔀 Queue has been shuffled.')

    @commands.command(name='play', aliases=('pl', 'p'))
    async def play_song(self, ctx: Context, *, query: str):
        """
        Add a song or a playlist to the queue.

        `query` **->** The song or playlist you wish to add.
        """

        player: mafic.Player = await self.get_player(ctx)

        await ctx.trigger_typing()
        try:
            tracks = await player.fetch_tracks(query)
        except (mafic.TrackLoadException, IndexError):
            return await ctx.reply(
                f'{ctx.denial} Must be a youtube link!'
            )

        if not tracks:
            return await ctx.send(f'> {ctx.denial} No tracks found.')
        elif isinstance(tracks, mafic.Playlist):
            for track in tracks.tracks:
                self.queue.add_track(track, ctx.author)
            await ctx.reply(f'> 🎵 Playlist has been added. (`{len(tracks.tracks)} songs queued`)')
        else:
            track = tracks[0]
            length = track.length / 1000
            total_time = 0
            for entry in self.queue.queue[1:]:
                total_time += entry.track.length / 1000
            total_time += (player.current.length / 1000 if player.current else 0) - (player.position / 1000)
            total_time = int(total_time)

            em = disnake.Embed(
                description=f'[{track.title}]({track.uri})'
            )
            em.set_thumbnail(f'https://img.youtube.com/vi/{track.identifier}/mqdefault.jpg')
            em.set_author(name='Added to queue', icon_url=self.bot.user.display_avatar)
            em.add_field(
                name='Channel',
                value=track.author,
            )
            em.add_field(
                name='Song Duration',
                value=self.format_time(length),
            )
            time_until_play = datetime.now() + relativedelta(seconds=total_time)
            em.add_field(
                name='Estimated time until playing',
                value=utils.human_timedelta(time_until_play, suffix=False),
            )
            em.add_field(
                name='Position in queue',
                value='now' if len(self.queue.queue) == 0 else str(len(self.queue.queue)),
            )

            self.queue.add_track(track, ctx.author)
            await ctx.send(embed=em)

        if player.current is None:
            data = self.queue.get_latest_track()
            await player.play(data, volume=self.vol)

    @commands.command(name='disconnect', aliases=('leave', 'dc', 'exit'))
    async def disconnect_voice(self, ctx: Context):
        """Makes the bot leave the voice channel."""

        await self.check_dj(ctx)

        self.queue.reset()
        self.is_paused = False
        self.dj = None
        self.vol = 10

        await ctx.reply('> ⏏️ Bot disconnected.')

        player = await self.get_player(ctx)
        if player.current:
            await player.stop()
        await player.destroy()

    @commands.command(name='pause')
    async def pause_song(self, ctx: Context):
        """Pauses the currently playing song if any."""

        await self.check_dj(ctx)

        player = await self.get_player(ctx)

        if player.current is None:
            return await ctx.reply(f'{ctx.denial} No song is currently playing.')

        if self.is_paused is True:
            return await ctx.reply(f'{ctx.denial} The song is already paused.')

        await player.pause()
        self.is_paused = True

        await ctx.reply('> ⏸️ Paused the song.')

    @commands.command(name='resume')
    async def resume_song(self, ctx: Context):
        """Resumes the paused song."""

        await self.check_dj(ctx)

        if self.is_paused is False:
            return await ctx.reply(f'{ctx.denial} The song is not paused.')

        self.is_paused = False
        player = await self.get_player(ctx)

        if player.current is None:
            track = self.queue.get_latest_track()
            if track:
                await player.play(track, volume=self.vol)
            else:
                return await ctx.reply(f'{ctx.denial} The queue is empty. Nothing to resume!')
        else:
            await player.resume()

        await ctx.reply('> ▶️ Resumed the song.')

    @commands.command(name='stop')
    async def stop_song(self, ctx: Context):
        """Stops the currently playing song while also pausing the next song from playing."""

        await self.check_dj(ctx)

        player = await self.get_player(ctx)
        if player.current is None:
            return await ctx.reply(f'{ctx.denial} There is currently nothing playing.')

        self.is_paused = True
        await player.stop()
        await ctx.reply('> ⏹️ Song stopped.')

    @commands.command(name='skip', aliases=('s', 'sk'))
    async def skip_song(self, ctx: Context):
        """Skips the current song and plays the next one."""

        await self.check_dj(ctx)

        player = await self.get_player(ctx)
        await player.stop()
        self.is_paused = False

        await asyncio.sleep(.25)  # Wait .25s so that `.stop` can be picked up by `on_track_end`

        track = self.queue.get_latest_track()
        if track is None:
            return await ctx.reply(f'{ctx.denial} The queue is empty. Nothing to skip to!')

        await ctx.reply(f'> ⏭️ Song skipped. Now playing `{track.title}`')

    async def _loop_queue(self, ctx: Context):
        """Primary code for looping the queue."""

        await self.check_dj(ctx)

        if not self.queue.queue:
            return await ctx.reply(f'{ctx.denial} The queue is empty.')
        elif self.queue.is_looping() is True:
            return await ctx.reply(f'{ctx.denial} The queue is already looping.')
        elif self.queue.looped_song is not None:
            return await ctx.reply(f'{ctx.denial} You are already looping a song.')

        self.queue.loop()

        await ctx.reply('> 🔁 Started looping the queue.')

    async def _unloop_queue(self, ctx: Context):
        """Primary code for unlooping the queue."""

        await self.check_dj(ctx)

        if not self.queue.queue:
            return await ctx.reply(f'{ctx.denial} The queue is empty.')
        elif self.queue.is_looping() is False:
            return await ctx.reply(f'{ctx.denial} The queue is not looping.')

        self.queue.unloop()

        await ctx.reply(f'> {ctx.agree} Stopped looping the queue.')

    async def _loop_song(self, ctx: Context):
        """Primary code for looping a song."""

        await self.check_dj(ctx)

        player = await self.get_player(ctx)
        if player.current is None:
            return await ctx.reply(f'{ctx.denial} There is no song currently playing to loop.')
        elif self.queue.is_looping() is True:
            return await ctx.reply(f'{ctx.denial} The queue is already looping.')

        self.queue.looped_song = player.current

        await ctx.reply('> 🔂 Looped the current song.')

    async def _unloop_song(self, ctx: Context):
        """Primary code for unlooping a song."""

        await self.check_dj(ctx)

        player = await self.get_player(ctx)
        if player.current is None:
            return await ctx.reply(f'{ctx.denial} There is no song currently playing to unloop.')

        self.queue.looped_song = None

        await ctx.reply(f'> {ctx.agree} Stopped looping the song.')

    @commands.group(name='loop', aliases=('l',), invoke_without_command=True, case_insensitive=True)
    async def loop_song(self, ctx: Context):
        """Starts or stops looping the current song."""

        if self.queue.looped_song is None:
            await self._loop_song(ctx)
        else:
            await self._unloop_song(ctx)

    @commands.command(name='loopqueue', aliases=('lq', 'loopq', 'lqueue'))
    async def loop_queue(self, ctx: Context):
        """Starts or stops looping the queue."""

        if not self.queue.is_looping():
            await self._loop_queue(ctx)
        else:
            await self._unloop_queue(ctx)

    @commands.group(name='queue', aliases=('q',), invoke_without_command=True, case_insensitive=True)
    async def show_queue(self, ctx: Context):
        """Display the queue."""

        if not self.queue.queue:
            return await ctx.reply(f'{ctx.denial} The queue is empty.')

        entries = []
        for entry in self.queue.queue[1:]:
            entries.append(
                f'[{entry.track.title}]({entry.track.uri}) ({self.format_time(entry.track.length / 1000)}) '
                f'- `Requested By: {entry.user}`'
            )

        entry = self.queue.get_audio_data(0)
        description = '___Now Playing___\n' \
                      f'\u2800[{entry.track.title}]({entry.track.uri}) ' \
                      f'({self.format_time(entry.track.length / 1000)}) ' \
                      f'- `Requested by {entry.user}`\n\n'

        menu = utils.SimplePages(
            ctx, entries, per_page=15, compact=True,
            entries_name='songs', perma_desc=description
        )
        menu.embed.title = 'Here\'s the current queue:'
        menu.embed.color = None
        await menu.start()

    @show_queue.command(name='clear', aliases=('c',))
    async def queue_clear(self, ctx: Context):
        """Clears the queue."""

        await self.check_dj(ctx)

        if len(self.queue.queue) == 1:
            return await ctx.reply(f'{ctx.denial} The queue is empty.')

        self.queue._queue = [self.queue._queue[0]]

        await ctx.reply(f'> {ctx.agree} The queue has been cleared.')

    @show_queue.command(name='remove', aliases=('del', 'rm', 'r'))
    async def queue_remove_index(self, ctx: Context, index: int):
        """
        Remove a song at the given index (can be seen when
        doing the `!queue` command)

        `index` **->** The index of which to remove the song from.
        """

        if not self.queue.queue:
            return await ctx.reply(f'{ctx.denial} The queue is empty.')

        if index < 1:
            return await ctx.reply(f'{ctx.denial} Index cannot be less than 1.')

        song = self.queue.get_audio_data(index)
        if song is None:
            return await ctx.reply(f'{ctx.denial} Couldn\'t find the song at the given index.')

        if song.user != ctx.author:
            await self.check_dj(ctx)

        self.queue.remove_track(index)

        await ctx.reply(f'> {ctx.agree} Removed `{song.track.title}` from the queue.')

    @commands.command(name='nowplaying', aliases=('np', 'playing'))
    async def now_playing(self, ctx: Context):
        """See what song is currently playing."""

        player = await self.get_player(ctx)
        if player.current is None:
            return await ctx.reply(f'{ctx.denial} Nothing is currently playing.')
        elif self.is_paused:
            return await ctx.reply(f'{ctx.denial} The current song is paused.')

        user = self.queue.get_audio_data(0).user
        em = disnake.Embed(
            title='Now playing',
            description=f'[{player.current.title}]({player.current.uri}) - '
                        f'`Requested by {user}`'
        )
        em.set_thumbnail(f'https://img.youtube.com/vi/{player.current.identifier}/mqdefault.jpg')

        pos = int(player.position / 1000)
        length = int(player.current.length / 1000)
        remaining = datetime.now() + relativedelta(seconds=((length) - (pos)))

        em.add_field(
            name='Channel',
            value=player.current.author,
            inline=False
        )
        em.add_field(
            name='Time',
            value=f'{self.format_time(pos)} / {self.format_time(length)}',
            inline=False
        )
        em.add_field(
            name='Time Left',
            value=utils.human_timedelta(remaining, suffix=False),
            inline=False
        )

        await ctx.reply(embed=em)

    @play_song.before_invoke
    async def ensure_voice_chat(self, ctx: Context):
        if ctx.author.id != self.bot._owner_id:
            return
        elif ctx.author.voice is None:
            await ctx.reply(f'{ctx.denial} You are not connected to a voice chat.')
            raise commands.CheckFailure('Not connected to a vc.')
        elif ctx.guild.voice_client is not None:
            if ctx.guild.voice_client.channel.id != ctx.author.voice.channel.id:
                await ctx.send(f'{ctx.denial} You are not connected to the voice channel where the bot is playing.')
                raise commands.CheckFailure('Not connected to the vc where bot is playing.')

        if self.dj is None:
            self.dj = ctx.author

    @disconnect_voice.before_invoke
    @pause_song.before_invoke
    @resume_song.before_invoke
    @stop_song.before_invoke
    @skip_song.before_invoke
    @loop_song.before_invoke
    @loop_queue.before_invoke
    @queue_clear.before_invoke
    @queue_remove_index.before_invoke
    @now_playing.before_invoke
    @set_volume.before_invoke
    async def ensure_bot_voice_chat(self, ctx: Context):
        if ctx.guild.voice_client is None or ctx.guild.me.voice is None:
            await ctx.reply(f'{ctx.denial} The bot is not connected to a vc.')
            raise commands.CheckFailure('The bot is not conn to a vc.')
        else:
            await self.ensure_voice_chat(ctx)


def setup(bot: Ukiyo):
    bot.add_cog(Music(bot))