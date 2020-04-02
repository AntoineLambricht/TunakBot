import logging
import sys
import traceback

from discord.ext import commands
from discord.ext.commands import Context
from discord import VoiceChannel, VoiceClient, VoiceState
from discord import Message, TextChannel, Emoji
from discord import Guild, Client, RawReactionActionEvent
from discord import Member
from discord import ChannelType
from discord.ext.commands import BotMissingPermissions

import music.music_icons as icons
from music import MusicPlayer
from exceptions.playlist_exceptions import *
from exceptions.download_exceptions import *
from exceptions.commands_exceptions import *
from utils.checks import is_playing, in_bot_voice_channel, is_paused, is_paused_or_playing

logger = logging.getLogger("tunak_bot")


class Music(commands.Cog):
    def __init__(self, bot: Client):
        self.bot: Client = bot
        self.players = {}

    # events
    def cog_unload(self):
        logger.info("Music Cog Unloaded")

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        """
            Delete all new messages in musics text channels
        """
        if message.channel.type == ChannelType.text:

            guild = message.guild
            message_channel: TextChannel = message.channel

            player: MusicPlayer = self.get_player(guild)

            if message_channel.id in player.text_channel_ids and message.author != self.bot.user:
                await message.delete()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        """
            Add action to different reaction button
        """
        channel: TextChannel = self.bot.get_channel(payload.channel_id)
        emoji: Emoji = payload.emoji
        message: Message = await channel.fetch_message(payload.message_id)
        user = self.bot.get_user(payload.user_id)

        if user != self.bot.user and message.author == self.bot.user:
            await message.remove_reaction(emoji, user)

            player = self.get_player(channel.guild)
            voice_client: VoiceClient = channel.guild.voice_client

            if voice_client is None:
                # TODO handle problem
                logger.warning("Bot not in a channel")
                return

            e = str(emoji)

            if e == icons.PREV:
                player.playlist.select_prev()
                await player.play_current_song()

            elif e == icons.PLAY:
                if voice_client.is_connected and voice_client.is_paused():
                    voice_client.resume()
                elif voice_client.is_connected and not voice_client.is_playing():
                    await player.play_current_song()

            elif e == icons.PAUSE:
                if voice_client.is_connected and voice_client.is_playing():
                    voice_client.pause()

            elif e == icons.STOP:
                if voice_client.is_connected and (voice_client.is_playing() or voice_client.is_paused()):
                    player.stop_without_continuing()

            elif e == icons.NEXT:
                player.playlist.select_next()
                await player.play_current_song()

            else:
                pass

            await player.update_playlist_messages()

    #################################################################
    # ---------------- Commands ----------------------------------- #
    #################################################################

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
            await sender_channel.connect()

    @commands.command()
    @commands.check(in_bot_voice_channel)
    async def leave(self, ctx: Context):
        player = self.get_player(ctx.guild)
        voice_client: VoiceClient = ctx.guild.voice_client
        if voice_client:
            player.stop_without_continuing()
            await voice_client.disconnect()
            await player.update_playlist_messages()

    @commands.command()
    @commands.check(in_bot_voice_channel)
    async def play(self, ctx: Context, *args):
        player: MusicPlayer = self.get_player(ctx.guild)
        voice_client: VoiceClient = ctx.guild.voice_client

        if len(args) == 0:
            if voice_client.is_connected and voice_client.is_paused():
                voice_client.resume()
            elif voice_client.is_connected and not voice_client.is_playing():
                await player.play_current_song()
        elif len(args) == 1:
            url = args[0]
            await player.add_song_from_url(url)

            player.playlist.select_last()
            await player.play_current_song()

            await player.update_playlist_messages()
        else:
            raise BadArgumentException("Too many arguments")
            pass

    @commands.command()
    async def add(self, ctx: Context, url: str):
        player: MusicPlayer = self.get_player(ctx.guild)
        await player.add_song_from_url(url)
        await player.update_playlist_messages()

    @commands.command()
    async def remove(self, ctx: Context, index: int):
        player = self.get_player(ctx.guild)
        player.playlist.remove(index)
        await player.update_playlist_messages()

    @commands.command()
    @commands.check(in_bot_voice_channel)
    @commands.check(is_paused_or_playing)
    async def stop(self, ctx: Context):
        player = self.get_player(ctx.guild)
        voice_client: VoiceClient = ctx.guild.voice_client

        if voice_client and voice_client.channel:
            player.stop_without_continuing()
            await player.update_playlist_messages()

    @commands.command()
    @commands.check(in_bot_voice_channel)
    @commands.check(is_playing)
    async def pause(self, ctx: Context):
        player = self.get_player(ctx.guild)
        voice_client: VoiceClient = ctx.guild.voice_client
        voice_client.pause()
        await player.update_playlist_messages()

    @commands.command()
    @commands.check(in_bot_voice_channel)
    @commands.check(is_paused)
    async def resume(self, ctx: Context):
        player = self.get_player(ctx.guild)
        voice_client: VoiceClient = ctx.guild.voice_client
        voice_client.resume()
        await player.update_playlist_messages()

    @commands.command()
    @commands.check(in_bot_voice_channel)
    async def next(self, ctx: Context):
        player = self.get_player(ctx.guild)
        player.playlist.select_next()
        await player.play_current_song()
        await player.update_playlist_messages()

    @commands.command()
    @commands.check(in_bot_voice_channel)
    async def prev(self, ctx: Context):
        player = self.get_player(ctx.guild)
        player.playlist.select_prev()
        await player.play_current_song()
        await player.update_playlist_messages()

    @commands.command()
    async def playlist(self, ctx: Context):
        player = self.get_player(ctx.guild)
        await ctx.send(embed=player.get_embed())

    @commands.command(name="setMusicChannel", aliases=["smc"])
    @commands.bot_has_permissions(manage_messages=True)
    async def set_music_channel(self, ctx: Context):
        await ctx.send("Waring, this text channel will be managed by me, "
                       "all message sent will be deleted !(but commands will be performed)")
        player = self.get_player(ctx.guild)
        player.text_channel_ids.append(ctx.channel.id)
        await player.update_playlist_messages()

    @commands.command(name="unsetMusicChannel", aliases=["umc"])
    async def unset_music_channel(self, ctx: Context):
        player = self.get_player(ctx.guild)
        player.text_channel_ids.remove(ctx.channel.id)
        await ctx.send("This text channel will no longer be managed by me!")

    @commands.command()
    async def goto(self, ctx: Context, playlist_id: int):
        player: MusicPlayer = self.get_player(ctx.guild)
        player.playlist.select(playlist_id)
        await player.play_current_song()
        await player.update_playlist_messages()

    #################################################################
    # ---------------- Errors ------------------------------------- #
    #################################################################
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
    @join.error
    @unset_music_channel.error
    @set_music_channel.error
    async def default_error(self, ctx: Context, error):
        if isinstance(error, commands.CommandInvokeError):
            error = error.original
        author: Member = ctx.author
        if isinstance(error, EmptyPlaylistException):
            await author.send("This playlist is empty.")
        if isinstance(error, NotInPlaylistException):
            await author.send("DEFAULT ERROR MESSAGE: NotInPlaylistException")
        if isinstance(error, AlreadyInPlaylistException):
            await author.send("DEFAULT ERROR MESSAGE: AlreadyInPlaylistException")
        if isinstance(error, EndOfPlaylistException):
            await author.send("DEFAULT ERROR MESSAGE : EndOfPlaylistException")
        if isinstance(error, FileTooBigException):
            await author.send("This file is too big to be downloaded!")
        if isinstance(error, BotMissingPermissions):
            await author.send("This file is too big to be downloaded!")
        else:
            exc = sys.exc_info()[1]
            tb: traceback = sys.exc_info()[2]
            for line in traceback.format_tb(tb):
                logger.error(line)

            tb: traceback = tb.tb_next
            for line in traceback.format_tb(tb):
                logger.error(line)
            logger.error(exc)

    #################################################################
    # ---------------- Functions ---------------------------------- #
    #################################################################

    # util methods
    # async def add_song_from_url(self, player, url):
    #
    #     youtube_id = yt_dl.parse_url(url)
    #
    #     player.playlist.add(await Song.from_id(youtube_id))

    # def stop_without_coninuing(self, voice_client: VoiceClient, player: MusicPlayer):
    #     if voice_client.is_connected() and (voice_client.is_playing() or voice_client.is_paused()):
    #         player.stop_after = True
    #         voice_client.stop()

    # def get_embed(self, guild: Guild) -> Embed:
    #     player = self.get_player(guild)
    #     voice_client: VoiceClient = guild.voice_client
    #     message = player.playlist.print()
    #     status = "Stoped"
    #     if voice_client:
    #         if voice_client.is_playing():
    #             status = 'Playing'
    #         elif voice_client.is_paused():
    #             status = 'Paused'
    #
    #     try:
    #         current = player.playlist.get_current()
    #         embed_data = {
    #             "title": f"Playlist - {status}",
    #             "description": message,
    #             "thumbnail": {
    #                 "url": current.thumbnail
    #             },
    #         }
    #     except EmptyPlaylistException:
    #         embed_data = {
    #             "title": f"Playlist - {status}",
    #             "description": message,
    #         }
    #
    #     return Embed.from_dict(embed_data)

    # async def update_playlist_messages(self, player: MusicPlayer):
    #     for channel_id in player.text_channel_ids:
    #         channel: TextChannel = await self.bot.fetch_channel(channel_id)
    #         messages = await channel.history(limit=1).flatten()
    #         last_message = messages[0]
    #
    #         if last_message.author == self.bot.user and last_message.embeds \
    #                 and last_message.embeds[0].title.startswith("Playlist"):
    #             await last_message.edit(embed=self.get_embed(channel.guild))
    #         else:
    #             playlist_message = await channel.send(embed=self.get_embed(channel.guild))
    #             await asyncio.gather(
    #                 playlist_message.add_reaction(ICONS.PREV),
    #                 playlist_message.add_reaction(ICONS.PLAY),
    #                 playlist_message.add_reaction(ICONS.PAUSE),
    #                 playlist_message.add_reaction(ICONS.STOP),
    #                 playlist_message.add_reaction(ICONS.NEXT)
    #             )

    # async def toggle_play_pause(self, voice_client: VoiceClient, player: MusicPlayer):
    #     if voice_client and voice_client.is_connected():
    #         if voice_client.is_paused():
    #             voice_client.resume()
    #         elif voice_client.is_playing():
    #             voice_client.pause()
    #         else:
    #             await self.play_current_song(voice_client, player)

    def get_player(self, guild: Guild) -> MusicPlayer:
        if guild.id not in self.players:
            self.players[guild.id] = MusicPlayer(self.bot, guild)

        return self.players[guild.id]

    # async def play_current_song(self, voice_client: VoiceClient, player: MusicPlayer):
    #     self.stop_without_coninuing(voice_client, player)
    #     try:
    #         current_song: Song = player.playlist.get_current()
    #         source = PCMVolumeTransformer(FFmpegPCMAudio(current_song.file_name, options='-vn'), 0.5)
    #
    #         def after(error):
    #             if error:
    #                 logger.error(error)
    #                 sys.exit(-1)
    #
    #             if player.stop_after:
    #                 player.stop_after = False
    #                 return
    #
    #             if player.auto_play_next and self.bot.loop.is_running():
    #                 player.playlist.select_next()
    #                 c1 = self.play_current_song(voice_client, player)
    #                 c2 = self.update_playlist_messages(player)
    #
    #                 fut1 = asyncio.run_coroutine_threadsafe(c1, self.bot.loop)
    #                 fut2 = asyncio.run_coroutine_threadsafe(c2, self.bot.loop)
    #                 try:
    #                     fut1.result()
    #                     fut2.result()
    #                 except Exception as err:
    #                     logger.error(err)
    #         voice_client.play(source, after=after)
    #     except EmptyPlaylistException:
    #         # if the playlist is empty: do nothing
    #         pass


def setup(bot):
    bot.add_cog(Music(bot))


def teardown(bot: commands.Bot):
    bot.remove_cog("Music")
