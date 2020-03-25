import logging
from audio_sources.youtube_source import get_data_and_download_if_not_in_cache


logger = logging.getLogger("tunak_bot")


class Song():
    def __init__(self, yt_id, url, title, thumbnail, file_name):
        self.yt_id = yt_id
        self.url = url
        self.file_name = file_name
        self.title = title
        self.thumbnail = thumbnail

    def __eq__(self, other):
        return self.yt_id == other.yt_id

    @classmethod
    async def from_id(cls, yt_id) -> 'Song':
        url = f'https://www.youtube.com/watch?v={yt_id}'
        data, file_name = await get_data_and_download_if_not_in_cache(yt_id)
        return cls(yt_id, url, data["title"], data["thumbnail"], file_name)
