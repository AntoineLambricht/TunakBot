import logging
import asyncio

from discord import Client
from discord import Guild
from discord import VoiceClient, TextChannel, Embed
from discord import PCMVolumeTransformer, FFmpegPCMAudio

from utils import db
from utils import yt_dl

from exceptions.playlist_exceptions import EmptyPlaylistException

import music.music_icons as ICONS

from . import Song
from . import Playlist

logger = logging.getLogger("tunak_bot")


class MusicPlayer:

    def __init__(self, bot: Client,
                 guild: Guild,
                 volume: float = 0.5,
                 playlist: Playlist = None,
                 text_channel_ids: list = None,
                 auto_play_next=True):

        self.bot = bot
        self.guild = guild
        self.auto_play_next = auto_play_next
        self.stop_after = False
        self.volume = volume
        self.text_channel_ids = list() if text_channel_ids is None else text_channel_ids

        if playlist is not None:
            self.playlist = playlist
        else:
            playlist_id = db.get_or_create_default_playlist(guild.id)[0]
            all_songs = db.get_all_songs_from_playlist_id(playlist_id)
            song_list = list()
            for s in all_songs:
                song_list.append(Song(s[1], s[3], s[4], s[2]))

            self.playlist = Playlist(playlist_id, guild, song_list=song_list)

    async def add_song_from_url(self, url):
        """
            Add a song to the playlist
        """
        youtube_id = yt_dl.parse_url(url)
        self.playlist.add(await Song.from_id(youtube_id))

    def stop_without_continuing(self):
        """
            Stop the player without passing to the next song (like a stop button)
        """
        voice_client: VoiceClient = self.guild.voice_client
        if voice_client.is_connected() and (voice_client.is_playing() or voice_client.is_paused()):
            self.stop_after = True
            voice_client.stop()

    async def play_current_song(self):
        """
            Play the current song of the playlist
        """
        self.stop_without_continuing()
        try:
            current_song: Song = self.playlist.get_current()
            source = PCMVolumeTransformer(FFmpegPCMAudio(current_song.file_name, options='-vn'), 0.5)

            def after(error):
                if error:
                    logger.error(error)
                    # sys.exit(-1)

                if self.stop_after:
                    self.stop_after = False
                    return

                if self.auto_play_next and self.bot.loop.is_running():
                    self.playlist.select_next()
                    c1 = self.play_current_song()
                    c2 = self.update_playlist_messages()

                    fut1 = asyncio.run_coroutine_threadsafe(c1, self.bot.loop)
                    fut2 = asyncio.run_coroutine_threadsafe(c2, self.bot.loop)
                    try:
                        fut1.result()
                        fut2.result()
                    except Exception as err:
                        logger.error(err)

            self.guild.voice_client.play(source, after=after)
        except EmptyPlaylistException:
            # if the playlist is empty: do nothing
            pass

    async def update_playlist_messages(self):
        """
            Update the last playlist message or send it if not existing
        """
        for channel_id in self.text_channel_ids:
            channel: TextChannel = await self.bot.fetch_channel(channel_id)
            messages = await channel.history(limit=1).flatten()
            last_message = messages[0]

            if last_message.author == self.bot.user and last_message.embeds \
                    and last_message.embeds[0].title.startswith("Playlist"):
                await last_message.edit(embed=self.get_embed())
            else:
                playlist_message = await channel.send(embed=self.get_embed())
                await asyncio.gather(
                    playlist_message.add_reaction(ICONS.PREV),
                    playlist_message.add_reaction(ICONS.PLAY),
                    playlist_message.add_reaction(ICONS.PAUSE),
                    playlist_message.add_reaction(ICONS.STOP),
                    playlist_message.add_reaction(ICONS.NEXT)
                )

    def get_embed(self) -> Embed:
        """
            Get the embed message for the playlist
        """
        voice_client: VoiceClient = self.guild.voice_client
        message = self.playlist.print()
        status = "Stoped"
        if voice_client:
            if voice_client.is_playing():
                status = 'Playing'
            elif voice_client.is_paused():
                status = 'Paused'

        try:
            current = self.playlist.get_current()
            embed_data = {
                "title": f"Playlist - {status}",
                "description": message,
                "thumbnail": {
                    "url": current.thumbnail
                },
            }
        except EmptyPlaylistException:
            embed_data = {
                "title": f"Playlist - {status}",
                "description": message,
            }

        return Embed.from_dict(embed_data)