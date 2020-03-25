import logging
import asyncio
import sys
from urllib.parse import parse_qs, urlparse

from discord.ext import commands
from discord.ext.commands import Context
from discord import VoiceChannel, VoiceClient, VoiceState
from discord import Embed, Message, TextChannel, Emoji
from discord import Guild, Client, RawReactionActionEvent

from audio_sources.youtube_source import YoutubeSource

import music.music_icons as ICONS
from music import Song, MusicPlayer
from music.playlist import EmptyPlaylistException

logger = logging.getLogger("tunak_bot")


async def is_playing(ctx: Context):
    voice_client: VoiceClient = ctx.guild.voice_client
    if voice_client and voice_client.is_connected() and voice_client.is_playing():
        return True
    else:
        raise commands.CommandError("Not currently playing.")


async def is_paused(ctx: Context):
    voice_client: VoiceClient = ctx.guild.voice_client
    if voice_client and voice_client.is_connected() and voice_client.is_paused():
        return True
    else:
        raise commands.CommandError("Not currently paused.")


async def is_paused_or_playing(ctx: Context):
    voice_client: VoiceClient = ctx.guild.voice_client
    if voice_client and voice_client.is_connected() \
            and (voice_client.is_paused() or voice_client.is_playing()):
        return True
    else:
        raise commands.CommandError("Not currently playing or paused.")


async def in_bot_voice_channel(ctx):
    sender_voice_state = ctx.author.voice
    voice_client: VoiceClient = ctx.guild.voice_client
    if ((sender_voice_state and voice_client)
            and (sender_voice_state.channel and voice_client.channel)
            and (sender_voice_state.channel == voice_client.channel)):
        return True
    else:
        raise commands.CommandError(
            "You need to be in the same channel as the bot to do that.")


class Music(commands.Cog):
    def __init__(self, bot: Client):
        self.bot: Client = bot
        self.players = {}

    # events
    def cog_unload(self):
        logger.info("Music Cog Unloaded")

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        guild = message.guild
        player: MusicPlayer = self.get_player(guild)
        message_channel: TextChannel = message.channel
        if message_channel.id in player.text_channel_ids and message.author != self.bot.user:
            await message.delete()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        channel: TextChannel = self.bot.get_channel(payload.channel_id)
        player = self.get_player(channel.guild)
        voice_client: VoiceClient = channel.guild.voice_client
        emoji: Emoji = payload.emoji
        message: Message = await channel.fetch_message(payload.message_id)
        user = self.bot.get_user(payload.user_id)
        if user != self.bot.user:
            await message.remove_reaction(emoji, user)
            e = str(emoji)

            if e == ICONS.PREV:
                player.playlist.select_prev()
                await self.play_current_song(voice_client, player)

            elif e == ICONS.PLAY:
                if voice_client.is_connected and voice_client.is_paused():
                    voice_client.resume()
                elif voice_client.is_connected and not voice_client.is_playing():
                    await self.play_current_song(voice_client, player)

            elif e == ICONS.PAUSE:
                if voice_client.is_connected and voice_client.is_playing():
                    voice_client.pause()

            elif e == ICONS.STOP:
                if voice_client.is_connected and (voice_client.is_playing() or voice_client.is_paused()):
                    self.stop_without_coninuing(voice_client, player)

            elif e == ICONS.NEXT:
                player.playlist.select_next()
                await self.play_current_song(voice_client, player)
            else:
                pass
            await self.update_playlist_messages(player)
    # commands
    @commands.command()
    async def join(self, ctx: Context):
        voice_client: VoiceClient = ctx.guild.voice_client

        sender_voice_state: VoiceState = ctx.message.author.voice
        if sender_voice_state is None:
            raise commands.CommandError("You are not in a voice channel")

        sender_channel: VoiceChannel = sender_voice_state.channel

        if voice_client and voice_client.is_connected():
            voice_client.pause()
            await voice_client.move_to(sender_channel)
            voice_client.resume()
        else:
            voice_client = await sender_channel.connect()

    @commands.command()
    @commands.check(in_bot_voice_channel)
    async def leave(self, ctx: Context):
        player = self.get_player(ctx.guild)
        voice_client: VoiceClient = ctx.guild.voice_client
        if voice_client:
            self.stop_without_coninuing(voice_client, player)
            await voice_client.disconnect()
            await self.update_playlist_messages(player)

    @commands.command()
    @commands.check(in_bot_voice_channel)
    async def play(self, ctx: Context, url: str):
        player: MusicPlayer = self.get_player(ctx.guild)

        await self.add_song_from_url(player, url)

        voice_client: VoiceClient = ctx.guild.voice_client

        player.playlist.select_last()
        await self.play_current_song(voice_client, player)

        await self.update_playlist_messages(player)

    @commands.command()
    async def add(self, ctx: Context, url: str):
        player: MusicPlayer = self.get_player(ctx.guild)
        await self.add_song_from_url(player, url)
        await self.update_playlist_messages(player)

    @commands.command()
    async def remove(self, ctx: Context, index: int):
        player = self.get_player(ctx.guild)
        player.playlist.remove(index)
        await self.update_playlist_messages(player)

    @commands.command()
    @commands.check(in_bot_voice_channel)
    @commands.check(is_paused_or_playing)
    async def stop(self, ctx: Context):
        player = self.get_player(ctx.guild)
        voice_client: VoiceClient = ctx.guild.voice_client

        if voice_client and voice_client.channel:
            # player.current = 0
            self.stop_without_coninuing(voice_client, player)
            await self.update_playlist_messages(player)
            # await voice_client.disconnect()

    @commands.command()
    @commands.check(in_bot_voice_channel)
    @commands.check(is_playing)
    async def pause(self, ctx: Context):
        player = self.get_player(ctx.guild)
        voice_client: VoiceClient = ctx.guild.voice_client
        voice_client.pause()
        await self.update_playlist_messages(player)

    @commands.command()
    @commands.check(in_bot_voice_channel)
    @commands.check(is_paused)
    async def resume(self, ctx: Context):
        player = self.get_player(ctx.guild)
        voice_client: VoiceClient = ctx.guild.voice_client
        voice_client.resume()
        await self.update_playlist_messages(player)

    @commands.command()
    @commands.check(in_bot_voice_channel)
    async def next(self, ctx: Context):
        player = self.get_player(ctx.guild)
        voice_client: VoiceClient = ctx.guild.voice_client

        player.playlist.select_next()
        await self.play_current_song(voice_client, player)

    @commands.command()
    @commands.check(in_bot_voice_channel)
    async def prev(self, ctx: Context):
        player = self.get_player(ctx.guild)
        voice_client: VoiceClient = ctx.guild.voice_client
        player.playlist.select_prev()
        await self.play_current_song(voice_client, player)

    @commands.command()
    async def playlist(self, ctx: Context):

        embed_message = self.get_embed(ctx.guild)

        message: Message = await ctx.send(embed=embed_message)
        await asyncio.gather(
            message.add_reaction(ICONS.PREV),
            message.add_reaction(ICONS.PLAY),
            message.add_reaction(ICONS.PAUSE),
            message.add_reaction(ICONS.STOP),
            message.add_reaction(ICONS.NEXT)
        )

    @commands.command(aliases=["smc"])
    async def setMusicChannel(self, ctx: Context):
        await ctx.send("""Waring, this text channel will be managed by me, all message sent will be deleted !(but commands will be performed)""")
        player = self.get_player(ctx.guild)
        player.text_channel_ids.append(ctx.channel.id)
        await self.update_playlist_messages(player)

    @commands.command()
    async def unsetMusicChannel(self, ctx: Context):
        await ctx.send("This text channel will no longer be managed by me!")
        player = self.get_player(ctx.guild)
        player.text_channel_ids.remove(ctx.channel.id)

    @commands.command()
    async def goto(self, ctx: Context, playlist_id: int):
        player: MusicPlayer = self.get_player(ctx.guild)
        voice_client: VoiceClient = ctx.guild.voice_client
        player.playlist.select(playlist_id)
        await self.play_current_song(voice_client, player)
        await self.update_playlist_messages(player)

    # error handling
    @play.error
    @add.error
    @remove.error
    @leave.error
    @stop.error
    @pause.error
    @playlist.error
    @prev.error
    @next.error
    @resume.error
    async def default_error(self, ctx, error):
        logger.error(error)

    @join.error
    async def join_error(self, ctx, error):
        if isinstance(error, commands.CommandError):
            await ctx.send(error)
        else:
            raise error

    # util methods
    async def add_song_from_url(self, player, url):
        # IDEA use t= query param to start at a moment

        parsed_url = urlparse(url)
        url_params = parse_qs(parsed_url.query)
        time = None
        if "t" in url_params:
            time = url_params["t"][0]

        if parsed_url.netloc == 'www.youtube.com':
            if "/v/" in parsed_url.path:
                youtube_id = parsed_url.path[3:]
            if "v" in url_params:
                youtube_id = url_params["v"][0]

        elif parsed_url.netloc != 'www.youtu.be':
            youtube_id = parsed_url.path[1:]

        if youtube_id is None:
            raise commands.ArgumentParsingError(
                "Not a valid format")  # TODO send message to user

        player.playlist.add(await Song.from_id(youtube_id))

    def stop_without_coninuing(self, voice_client: VoiceClient, player: MusicPlayer):
        if voice_client.is_connected() and (voice_client.is_playing() or voice_client.is_paused()):
            player.stop_after = True
            voice_client.stop()

    def get_embed(self, guild: Guild) -> Embed:
        player = self.get_player(guild)
        voice_client: VoiceClient = guild.voice_client
        message = player.playlist.print()
        status = "Stoped"
        if voice_client:
            if voice_client.is_playing():
                status = 'Playing'
            elif voice_client.is_paused():
                status = 'Paused'

        try:
            current = player.playlist.get_current()
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

    async def update_playlist_messages(self, player: MusicPlayer):
        for channel_id in player.text_channel_ids:
            channel: TextChannel = await self.bot.fetch_channel(channel_id)
            messages = await channel.history(limit=1).flatten()
            last_message = messages[0]

            if last_message.author == self.bot.user and last_message.embeds \
                    and last_message.embeds[0].title.startswith("Playlist"):
                await last_message.edit(embed=self.get_embed(channel.guild))
            else:
                playlist_message = await channel.send(embed=self.get_embed(channel.guild))
                await asyncio.gather(
                    playlist_message.add_reaction(ICONS.PREV),
                    playlist_message.add_reaction(ICONS.PLAY),
                    playlist_message.add_reaction(ICONS.PAUSE),
                    playlist_message.add_reaction(ICONS.STOP),
                    playlist_message.add_reaction(ICONS.NEXT)
                )

    async def toggle_play_pause(self, voice_client: VoiceClient, player: MusicPlayer):
        if voice_client and voice_client.is_connected():
            if voice_client.is_paused():
                voice_client.resume()
            elif voice_client.is_playing():
                voice_client.pause()
            else:
                await self.play_current_song(voice_client, player)

    def get_player(self, guild: Guild) -> MusicPlayer:
        if guild.id not in self.players:
            self.players[guild.id] = MusicPlayer(guild)

        return self.players[guild.id]

    async def play_current_song(self, voice_client: VoiceClient, player: MusicPlayer):
        self.stop_without_coninuing(voice_client, player)
        try:
            current_song: Song = player.playlist.get_current()
            source = await YoutubeSource.from_yt_id(current_song.yt_id)

            def after(error):
                if error:
                    logger.error(error)
                    sys.exit(-1)

                if player.stop_after:
                    player.stop_after = False
                    return

                if player.auto_play_next and self.bot.loop.is_running():
                    player.playlist.select_next()
                    c1 = self.play_current_song(voice_client, player)
                    c2 = self.update_playlist_messages(player)

                    fut1 = asyncio.run_coroutine_threadsafe(c1, self.bot.loop)
                    fut2 = asyncio.run_coroutine_threadsafe(c2, self.bot.loop)
                    try:
                        fut1.result()
                        fut2.result()
                    except Exception as err:
                        logger.error(err)
            voice_client.play(source, after=after)
        except EmptyPlaylistException:
            # if the playlist is empty: do nothing
            pass


def setup(bot):
    bot.add_cog(Music(bot))


def teardown(bot: commands.Bot):
    bot.remove_cog("Music")
