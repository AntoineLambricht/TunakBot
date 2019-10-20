import os
from os import path

import discord
from discord.ext import commands
TOKEN = os.environ.get("TUNAK_BOT_TOKEN")

bot = commands.Bot(command_prefix=".")

cogs_dir = "cogs"


@bot.event
async def on_ready():
    print("Online.")


@bot.command()
async def load(ctx: commands.Context, extension_name: str):
    try:
        bot.load_extension(extension_name)
    except (AttributeError, ImportError) as e:
        await ctx.send("```py\n{}: {}\n```".format(type(e).__name__, str(e)))
        return
    await ctx.send("{} loaded.".format(extension_name))


@bot.command()
async def unload(ctx: commands.Context, extension_name: str):
    bot.unload_extension(extension_name)
    await ctx.send("{} unloaded.".format(extension_name))


if __name__ == "__main__":
    bot.load_extension("cogs.music")
    bot.run(TOKEN)
