import sqlite3
import logging
import sys
from music import Song

logger = logging.getLogger("tunak_bot")

db_file_name = "music.db"
connection = None


def initialisation():

    sql_create_songs_table = """
    CREATE TABLE IF NOT EXISTS songs (
        id          INTEGER     PRIMARY KEY     ,
        yt_id       TEXT                        ,
        url         TEXT                        ,
        file_name   TEXT                        ,
        title       TEXT                        ,
        thumbnail   TEXT                        ,
        playlist_id INTEGER                     ,
        FOREIGN KEY(playlist_id) REFERENCES playlists(id)
    )
    """

    sql_create_playlist_table = """
    CREATE TABLE IF NOT EXISTS playlists (
        id          INTEGER     PRIMARY KEY ,
        name        TEXT                    ,
        guild_id    TEXT                    
    )

    """
    # FOREIGN KEY(guild_id) REFERENCES servers(guild_id)

    # sql_create_server_table = """
    # CREATE TABLE IF NOT EXISTS servers (
    #     guild_id    TEXT        NOT NULL,
    #     PRIMARY KEY(guild_id)
    # )
    # """

    conn = getConnection()
    c = conn.cursor()
    try:
        c.execute(sql_create_songs_table)
        c.execute(sql_create_playlist_table)
        # c.execute(sql_create_server_table)
        logger.info("DB initialized.")
    except sqlite3.Error as e:
        logger.error(e)
        sys.exit(-1)


def getConnection():
    try:
        global connection
        if not connection:
            connection = sqlite3.connect(db_file_name)
        return connection
    except sqlite3.Error as e:
        logger.error(e)


def get_or_create_default_playlist(guild_id):
    conn = getConnection()
    try:
        c = conn.cursor()
        c.execute("""SELECT * FROM playlists
                  WHERE name=? AND guild_id=?""",
                  ("default", guild_id))
        playlist = c.fetchone()
        if playlist is None:
            last_row_id = add_playlist(guild_id, "default")
            return (last_row_id, "default", guild_id)
        else:
            return playlist

    except sqlite3.Error as e:
        logger.error(e)
        sys.exit(-1)


def get_playlist(guild_id, playlist_name):
    conn = getConnection()
    try:
        c = conn.cursor()
        c.execute("""SELECT * FROM playlists
                  WHERE name=? AND guild_id=?""",
                  (playlist_name, guild_id))
        playlist = c.fetchone()
        return playlist
    except sqlite3.Error as e:
        logger.error(e)
        sys.exit(-1)


def add_song_to_playlist(song: Song, playlist_id):
    conn = getConnection()
    try:
        c = conn.cursor()
        c.execute("""INSERT INTO songs (yt_id,url,file_name,title,thumbnail,playlist_id)
                  VALUES (?,?,?,?,?,?)""",
                  (song.yt_id, song.url, song.file_name, song.title, song.thumbnail, playlist_id))
        conn.commit()
        return c.lastrowid
    except sqlite3.Error as e:
        logger.error(e)
        sys.exit(-1)


def remove_song_from_playlist(yt_id, playlist_id):
    conn = getConnection()
    try:
        c = conn.cursor()
        c.execute("""DELETE FROM songs WHERE playlist_id=? AND yt_id=?""",
                  (playlist_id, yt_id))
        conn.commit()
        return c.lastrowid
    except sqlite3.Error as e:
        logger.error(e)
        sys.exit(-1)


def get_all_songs_from_playlist_id(playlist_id):
    conn = getConnection()
    try:
        c = conn.cursor()
        c.execute("""SELECT * FROM songs
                    WHERE playlist_id=?""", (playlist_id,))
        all_songs = c.fetchall()
        return all_songs
    except sqlite3.Error as e:
        logger.error(e)
        sys.exit(-1)


def get_all_songs(guild_id, playlist_name="default"):
    conn = getConnection()
    try:
        c = conn.cursor()
        c.execute("""SELECT * FROM songs s, playlists p
                    WHERE p.name=?
                    AND p.guild_id=?
                    AND s.playlist_id = p.id """,
                  (playlist_name, guild_id))
        all_songs = c.fetchall()
        return all_songs
    except sqlite3.Error as e:
        logger.error(e)
        sys.exit(-1)


def add_playlist(guild_id, playlist_name):
    conn = getConnection()
    try:
        c = conn.cursor()
        c.execute("""INSERT INTO playlists (name,guild_id)
                  VALUES (?,?)""",
                  (playlist_name, guild_id))
        conn.commit()
        return c.lastrowid
    except sqlite3.Error as e:
        logger.error(e)
        sys.exit(-1)
