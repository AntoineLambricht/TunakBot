import logging
from utils import yt_dl


logger = logging.getLogger("tunak_bot")


class Song:
    def __init__(self, yt_id, title, thumbnail, file_name):
        self.yt_id = yt_id
        self.file_name = file_name
        self.title = title
        self.thumbnail = thumbnail

    def __eq__(self, other):
        return self.yt_id == other.yt_id

    @classmethod
    async def from_id(cls, yt_id) -> 'Song':
        data = await yt_dl.get_data(yt_id)
        return cls(yt_id, data["title"], data["thumbnail"], data["file_name"])
