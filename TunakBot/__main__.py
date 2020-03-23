import os
import sys
import logging
import coloredlogs
from discord.ext import commands

bot = commands.Bot(command_prefix=".")

@bot.event
async def on_connect():
    logger.info("Connected.")


@bot.event
async def on_ready():
    logger.info("Online.")


@bot.event
async def on_error(event, *args, **kwargs):
    logger.error(event, args, kwargs)


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
    TOKEN = os.environ.get("TUNAK_BOT_TOKEN")
    logger = logging.getLogger("tunak_bot")
    coloredlogs.install(fmt="%(levelname)s: %(message)s", logger=logger)

    if not TOKEN:
        logger.error("Token is empty!")
        sys.exit(-1)

    COGS_DIR = "cogs"
    bot.load_extension("cogs.music")
    LOOP = bot.loop
    try:
        LOOP.run_until_complete(bot.start(TOKEN))
    except KeyboardInterrupt:
        logger.info("Exiting...")
        LOOP.run_until_complete(bot.logout())
        # cancel all tasks lingering
    finally:
        LOOP.close()
