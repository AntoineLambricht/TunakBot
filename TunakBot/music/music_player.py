from . import Playlist


class MusicPlayer():

    def __init__(self, volume: float = 0.5, playlist: Playlist = Playlist(), playlist_text_channel: list = None):
        self.volume = volume
        self.playlist = playlist
        if playlist_text_channel is None:
            self.playlist_text_channel = list()
        else:
            self.playlist_text_channel = playlist_text_channel

    @classmethod
    def from_db(cls, db_player) -> 'MusicPlayer':
        return cls(db_player.volume, Playlist(db_player.current_playlist), db_player.playlist_text_channel)
