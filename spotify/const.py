DOWNLOAD_DIR = "rds/"
OUTPUT_DIR = "rds/"
AUDIO_QUALITY = "high"
AUDIO_CODEC = "ogg"
AUDIO_BITRATE = "160k"
DATA_CHUNK_SIZE = 20000

CODEC_MAP = {
    'aac': 'aac',
    'fdk_aac': 'libfdk_aac',
    'm4a': 'aac',
    'mp3': 'libmp3lame',
    'ogg': 'copy',
    'opus': 'libopus',
    'vorbis': 'copy',
}
EXT_MAP = {
    'aac': 'm4a',
    'fdk_aac': 'm4a',
    'm4a': 'm4a',
    'mp3': 'mp3',
    'ogg': 'ogg',
    'opus': 'ogg',
    'vorbis': 'ogg',
}

CREDENTIAL_LOCATION = "spotify/credentials/credentials.json"

TRACKS_URL = 'https://api.spotify.com/v1/tracks'
TRACK_STATS_URL = 'https://api.spotify.com/v1/audio-features/'
PLAYLISTS_URL = 'https://api.spotify.com/v1/playlists'
ALBUM_URL = 'https://api.spotify.com/v1/albums'

TRACKNUMBER = 'tracknumber'
USER_READ_EMAIL = 'user-read-email'
USER_FOLLOW_READ = 'user-follow-read'
PLAYLIST_READ_PRIVATE = 'playlist-read-private'
USER_LIBRARY_READ = 'user-library-read'

LIMIT = 'limit'
OFFSET = 'offset'
TYPE = 'type'
USER_LANGUAGE = "en"