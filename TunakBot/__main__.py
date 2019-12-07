import os
from discord.ext import commands

import database


TOKEN = os.environ.get("TUNAK_BOT_TOKEN")

bot = commands.Bot(command_prefix=".")

COGS_DIR = "cogs"


@bot.event
async def on_connect():
    print("Connected.")


@bot.event
async def on_ready():
    print("Online.")


@bot.event
async def on_error(event, *args, **kwargs):
    print(event, args, kwargs)


@bot.command()
async def load(ctx: commands.Context, extension_name: str):
    try:
        bot.load_extension(extension_name)
    except (AttributeError, ImportError) as error:
        await ctx.send("```py\n{}: {}\n```".format(type(error).__name__, str(error)))
        return
    await ctx.send("{} loaded.".format(extension_name))


@bot.command()
async def unload(ctx: commands.Context, extension_name: str):
    bot.unload_extension(extension_name)
    await ctx.send("{} unloaded.".format(extension_name))


if __name__ == "__main__":
    # database.init()
    bot.load_extension("cogs.music")
    LOOP = bot.loop
    try:
        LOOP.run_until_complete(bot.start(TOKEN))
    except KeyboardInterrupt:
        print("Exiting...")
        LOOP.run_until_complete(bot.logout())
        # cancel all tasks lingering
    finally:
        LOOP.close()
