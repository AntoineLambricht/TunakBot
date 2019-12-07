from audio_sources.youtube_source import YoutubeSource


class Song():
    def __init__(self, yt_id, url, data, file_name):
        self.yt_id = yt_id
        self.url = url
        self.data = data
        self.file_name = file_name
        self.title = data.get('title')
        self.thumbnail = data.get('thumbnail')

    def __eq__(self, other):
        return self.yt_id == other.yt_id

    @classmethod
    async def from_id(cls, yt_id) -> 'Song':
        url = f'https://www.youtube.com/watch?v={yt_id}'
        data, file_name = await YoutubeSource.get_data(yt_id)
        return cls(yt_id, url, data, file_name)
