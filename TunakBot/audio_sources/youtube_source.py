import asyncio
import os
import os.path as path
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
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
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
        download = True
        file_name = f"{MUSIC_FOLDER}{yt_id}.webm"
        url = f"https://www.youtube.com/watch?v={yt_id}"
        if path.isfile(file_name) and os.access(file_name, os.R_OK):
            download = False

        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=True))
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        if download:
            file_name = ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(file_name, **ffmpeg_options), data=data)

    # @classmethod
    # async def _from_file(cls, file_name, url, loop=None):
    #     loop = loop or asyncio.get_event_loop()
    #     data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
    #     if 'entries' in data:
    #         # take first item from a playlist
    #         data = data['entries'][0]

    #     return cls(discord.FFmpegPCMAudio(file_name, **ffmpeg_options), data=data)

    # @classmethod
    # async def _from_yt_url(cls, url, *, loop=None):

    @classmethod
    async def get_data(cls, yt_id, loop=None):
        download = True
        file_name = f"{MUSIC_FOLDER}{yt_id}.webm"
        url = f"https://www.youtube.com/watch?v={yt_id}"
        if path.isfile(file_name) and os.access(file_name, os.R_OK):
            download = False
        loop = loop or asyncio.get_event_loop()
        if download:
            logger.debug("Downloading...")
        else:
            logger.debug("Fecthing data...")
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download))
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
        if download:
            file_name = ytdl.prepare_filename(data)
        return data, file_name
