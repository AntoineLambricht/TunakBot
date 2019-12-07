from functools import singledispatch
from .song import Song


class EmptyPlaylistException(Exception):
    pass


class AlreadyInPlaylistException(Exception):
    pass


class NotInPlaylistException(Exception):
    pass


class EndOfPlaylistException(Exception):
    pass


class Playlist():
    def __init__(self, song_list: list = None):
        if song_list is None:
            self.song_list = list()
        else:
            self.song_list = song_list
        self.song_list = song_list
        self.current = -1
        self.loop = True

        self.remove = singledispatch(self.remove)
        self.remove.register(str, self._remove_with_url)
        self.remove.register(int, self._remove_with_id)

    def add(self, song: Song) -> None:
        if song in self.song_list:
            raise AlreadyInPlaylistException()
        if self.get_len() == 0:
            self.current = 0

        self.song_list.append(song)

    def remove(self, identifier):
        raise TypeError(f"This type isn't supported: {type(identifier)}")

    def _remove_with_url(self, yt_id: str):
        try:
            self.song_list.remove(yt_id)
            if self.current >= self.get_len():
                self.select_last()
        except ValueError:
            raise NotInPlaylistException

    def _remove_with_id(self, number: int):
        if 0 <= number < self.get_len():
            del self.song_list[number]
            if self.current >= self.get_len():
                self.select_last()
        else:
            raise NotInPlaylistException

    def select_next(self):
        if self.get_len() == 0:
            raise EmptyPlaylistException
        temp = self.current + 1
        if temp >= self.get_len():
            if self.loop:
                self.select_first()
            else:
                raise EndOfPlaylistException
        else:
            self.current = temp

    def select_prev(self):
        if self.get_len() == 0:
            raise EmptyPlaylistException()
        temp = self.current - 1
        if temp == -1:
            if self.loop:
                self.select_last()
            else:
                raise EndOfPlaylistException
        else:
            self.current = temp

    def select_last(self):
        self.select(self.get_len()-1)

    def select_first(self):
        self.select(0)

    def select(self, selection: int):
        if 0 <= selection < len(self.song_list):
            self.current = selection
        else:
            raise NotInPlaylistException

    def get_current(self) -> Song:
        if self.current >= 0:
            return self.song_list[self.current]
        else:
            raise EmptyPlaylistException

    def get_len(self) -> int:
        return len(self.song_list)

    def print(self) -> str:
        if self.get_len() > 0:
            lines = []
            for index, song in enumerate(self.song_list):
                if index == self.current:
                    lines.append(f' -> {index} - {song.title}\n')
                else:
                    lines.append(f'    {index} - {song.title}\n')
            return "".join(lines)
        else:
            return "Empty playlist"