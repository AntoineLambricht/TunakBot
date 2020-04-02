import asyncio
import logging
import urllib

from pytube import Stream
from pytube import YouTube
from exceptions.download_exceptions import *

MUSIC_FOLDER = './musics/'

logger = logging.getLogger("tunak_bot")


def parse_url(url):
    # TODO use "t" parameter to start at a certain time
    parsed_url = urllib.urlparse(url)
    url_params = urllib.parse_qs(parsed_url.query)
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
        raise WrongUrlFormatException("Not a valid format")

    return youtube_id


async def get_data(yt_id):
    youtube = YouTube(f'https://www.youtube.com/watch?v={yt_id}')

    title = youtube.title
    thumbnail = youtube.thumbnail_url
    length = youtube.length
    if length > 1000:
        raise FileTooBigException("This file is too big")
    loop = asyncio.get_event_loop()
    stream: Stream = select_stream(youtube.streams)
    file_name = await loop.run_in_executor(None, lambda: stream.download(output_path=MUSIC_FOLDER, filename=yt_id))
    data = {"title": title, "url": f'https://www.youtube.com/watch?v={yt_id}',
            "thumbnail": thumbnail, "file_name": file_name}
    return data


def select_stream(streams) -> Stream:
    """
        Select the best audio stream
    """
    return streams.filter(only_audio=True).order_by('abr')[-1]
