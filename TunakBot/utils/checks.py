from discord.ext import commands
from discord.ext.commands import Context
from discord import VoiceClient


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
        raise commands.CommandError("You need to be in the same channel as the bot to do that.")

