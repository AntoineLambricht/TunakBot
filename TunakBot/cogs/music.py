import discord
from discord.ext import commands
from discord.ext.commands import Context
from discord import VoiceChannel, VoiceClient, Message, Guild
from AudioSources.YTDLSource import YTDLSource


class MusicPlayer():
    def __init__(self):
        self.volume = 0.5
        self.playlist = []
        self.current = 0
        self.loop = True

    def next(self):
        if len(self.playlist) == 0:
            return False
        self.current += 1
        if self.current >= len(self.playlist):
            if self.loop:
                self.current = 0
            else:
                return False
        return True

    def prev(self):
        if len(self.playlist) == 0:
            return False
        self.current -= 1
        if self.current < 0:
            if self.loop:
                self.current = len(self.playlist)-1
            else:
                self.current = 0
                return False
        return True


async def is_playing_audio(ctx: Context):
    voice_client: VoiceClient = ctx.guild.voice_client
    if voice_client and voice_client.channel and voice_client.source:
        return True
    else:
        raise commands.CommandError("Not currently playing audio")


async def in_voice_channel(ctx):
    voice_state = ctx.author.voice
    voice_client: VoiceClient = ctx.guild.voice_client
    if (voice_state and voice_client) and (voice_state.channel and voice_client.channel) and (voice_state.channel == voice_client.channel):
        return True
    else:
        raise commands.CommandError(
            "You need to be in the channel to do that.")


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.players = {}

    @commands.command()
    @commands.guild_only()
    async def play(self, ctx: Context, url: str):
        player = self.getPlayer(ctx.guild)
        voice_client: VoiceClient = ctx.guild.voice_client

        if voice_client and voice_client.is_playing():
            source = await YTDLSource.from_url(url, loop=self.bot.loop)
            player.playlist.append(source)
        else:
            voice_state = ctx.message.author.voice
            if voice_state is None:
                raise commands.CommandError("You are not in a voice channel")
            sender_voice_channel: VoiceChannel = voice_state.channel
            voice_client = await sender_voice_channel.connect()
            source = await YTDLSource.from_url(url, loop=self.bot.loop)
            player.playlist.append(source)
            self.playCurrentSong(voice_client, player)

    @commands.command()
    @commands.guild_only()
    @commands.check(is_playing_audio)
    @commands.check(in_voice_channel)
    async def stop(self, ctx: Context):
        player = self.getPlayer(ctx.guild)
        voice_client: VoiceClient = ctx.guild.voice_client

        if voice_client and voice_client.channel:
            player.current = 0
            await voice_client.disconnect()

    @commands.command()
    @commands.guild_only()
    @commands.check(is_playing_audio)
    @commands.check(in_voice_channel)
    async def pause(self, ctx: Context):
        # player = self.getPlayer(ctx.guild)
        voice_client: VoiceClient = ctx.guild.voice_client
        voice_client.pause()

    @commands.command()
    @commands.guild_only()
    @commands.check(is_playing_audio)
    @commands.check(in_voice_channel)
    async def resume(self, ctx: Context):
        # player = self.getPlayer(ctx.guild)
        voice_client: VoiceClient = ctx.guild.voice_client
        voice_client.resume()

    @commands.command()
    @commands.guild_only()
    @commands.check(is_playing_audio)
    @commands.check(in_voice_channel)
    async def next(self, ctx: Context):
        player = self.getPlayer(ctx.guild)
        voice_client: VoiceClient = ctx.guild.voice_client

        if player.next():
            self.playCurrentSong(voice_client, player)

    @commands.command()
    @commands.guild_only()
    @commands.check(is_playing_audio)
    @commands.check(in_voice_channel)
    async def prev(self, ctx: Context):
        player = self.getPlayer(ctx.guild)
        voice_client: VoiceClient = ctx.guild.voice_client

        if player.prev():
            self.playCurrentSong(voice_client, player)

    @commands.command()
    @commands.guild_only()
    async def playlist(self, ctx: Context):
        player = self.getPlayer(ctx.guild)
        # voice_client: VoiceClient = ctx.guild.voice_client
        m = "Current : {}\n".format(player.current)

        for num, song in enumerate(player.playlist, start=0):
            m += "{}: {}\n".format(num, song.title)

        await ctx.send(m)

    def getPlayer(self, guild: Guild) -> MusicPlayer:
        if guild.id not in self.players:
            self.players[guild.id] = MusicPlayer()
        return self.players[guild.id]

    def playCurrentSong(self, voiceClient: VoiceClient, player: MusicPlayer):
        if len(player.playlist) == 0:  # TODO HANDLE STOP
            return
        source = player.playlist[player.current]

        def aftersong(err):
            if err:
                raise err
            if player.next():
                self.playCurrentSong(voiceClient, player)
        voiceClient.stop()
        voiceClient.play(source, after=aftersong)


def setup(bot):
    bot.add_cog(Music(bot))


def teardown(bot: commands.Bot):
    bot.remove_cog("Music")
