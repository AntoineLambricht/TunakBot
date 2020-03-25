import asyncio
import os
import os.path
import logging

import discord
import youtube_dl

logger = logging.getLogger('tunak_bot')

MUSIC_FOLDER = './musics/'

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': MUSIC_FOLDER+'%(id)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': False,
    'cachedir': False,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'max_filesize': 10000000
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YoutubeSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_yt_id(cls, yt_id, loop=None):

        data, file_name = await get_data_and_download_if_not_in_cache(yt_id, loop)
        return cls(discord.FFmpegPCMAudio(file_name, **ffmpeg_options), data=data)


async def get_data_and_download_if_not_in_cache(yt_id, loop=None):

    download = True
    file_name = get_file_name_in_cache(yt_id)

    url = f"https://www.youtube.com/watch?v={yt_id}"
    if file_name and os.access(os.path.abspath(file_name), os.R_OK):
        download = False
    loop = loop or asyncio.get_event_loop()
    if download:
        logger.debug("Downloading...")
    else:
        logger.debug("Fecthing data...")

    data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=download))
    if download:
        logger.debug(data)
    if 'entries' in data:
        data = data['entries'][0]
    if download:
        logger.debug(file_name)
        file_name = ytdl.prepare_filename(data)
        logger.debug(file_name)
    return data, file_name


def get_file_name_in_cache(yt_id):
    dirs = os.listdir(MUSIC_FOLDER)
    for f in dirs:
        file_name, ext = os.path.splitext(f)
        if file_name == yt_id:
            return f"{MUSIC_FOLDER}{yt_id}{ext}"
    return None
