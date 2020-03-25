import logging
from discord import Guild
from database import db
from . import Song
from . import Playlist

logger = logging.getLogger("tunak_bot")


class MusicPlayer():

    def __init__(self, guild: Guild,
                 volume: float = 0.5,
                 playlist: Playlist = None,
                 text_channel_ids: list = None,
                 auto_play_next=True):
        self.auto_play_next = auto_play_next
        self.stop_after = False
        self.volume = volume
        self.text_channel_ids = list() if text_channel_ids is None else text_channel_ids
        if playlist is not None:
            self.playlist = playlist
        else:
            playlist_id = db.get_or_create_default_playlist(guild.id)[0]
            all_songs = db.get_all_songs_from_playlist_id(playlist_id)
            songlist = list()
            for s in all_songs:
                songlist.append(Song(s[1], s[2], s[4], s[5], s[3]))

            self.playlist = Playlist(playlist_id,
                                     guild,
                                     song_list=songlist)
