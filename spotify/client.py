import ffmpy
import json
import time
import requests
from pathlib import Path

from librespot.core import Session
from librespot.metadata import TrackId
from librespot.audio.decoders import AudioQuality
from librespot.audio.decoders import VorbisOnlyAudioQuality

from .const import *
MAX_RETRIES = 3

class Client():
    def __init__(self):
        quality_options = {
            'auto': AudioQuality.HIGH,
            'normal': AudioQuality.NORMAL,
            'high': AudioQuality.HIGH,
            'very_high': AudioQuality.VERY_HIGH
        }
        self.quality = quality_options[AUDIO_QUALITY]
        self.extension = EXT_MAP[AUDIO_CODEC]
        self.codec = CODEC_MAP[AUDIO_CODEC]
        self.bitrate = AUDIO_BITRATE
        self.language = USER_LANGUAGE
    
    def get_content_stream(self, content_id, quality):
        return self.SESSION.content_feeder().load(content_id, VorbisOnlyAudioQuality(quality), False, None)

    def __get_auth_token(self):
        tOken = self.SESSION.tokens().get_token(
            USER_READ_EMAIL, PLAYLIST_READ_PRIVATE, USER_LIBRARY_READ, USER_FOLLOW_READ
        ).access_token
        return tOken

    def get_auth_header(self):
        return {
            'Authorization': f'Bearer {self.__get_auth_token()}',
            'Accept-Language': f'{self.language}',
            'Accept': 'application/json',
            'app-platform': 'WebPlayer'
        }

    def get_auth_header_and_params(self, limit, offset):
        return {
            'Authorization': f'Bearer {self.__get_auth_token()}',
            'Accept-Language': f'{self.language}',
            'Accept': 'application/json',
            'app-platform': 'WebPlayer'
        }, {LIMIT: limit, OFFSET: offset}

    def login(self, cred_location, username, password):
        print("Logging into Spotify...")
        print(Path(cred_location))
        if Path(cred_location).is_file():
            try:
                print("upper")
                conf = Session.Configuration.Builder().set_store_credentials(False).build()
                self.SESSION = Session.Builder(conf).stored_file(cred_location).create()
                return 
            except RuntimeError:
                pass
        else:
            while True:
                try:
                    print("lower")
                    conf = Session.Configuration.Builder().set_stored_credential_file(cred_location).build()
                    self.SESSION = Session.Builder(conf).user_pass(username, password).create()
                    return
                except RuntimeError:
                    pass

    def invoke_url(self, url, tryCount=0):
        headers = self.get_auth_header()
        response = requests.get(url, headers=headers)
        responsetext = response.text
        try:
            responsejson = response.json()
        except json.decoder.JSONDecodeError:
            responsejson = {"error": {"status": "unknown", "message": "received an empty response"}}

        if not responsejson or 'error' in responsejson:
            if tryCount < (5 - 1):
                print(f"Spotify API Error (try {tryCount + 1}) ({responsejson['error']['status']}): {responsejson['error']['message']}")
                time.sleep(5)
                return self.invoke_url(url, tryCount + 1)

            print(f"Spotify API Error ({responsejson['error']['status']}): {responsejson['error']['message']}")
        return responsetext, responsejson

    def get_song_info(self, song_id):
        (raw, info) = self.invoke_url(f'{TRACKS_URL}?ids={song_id}&market=from_token')

        if not 'tracks' in info:
            raise ValueError(f'Invalid response from TRACKS_URL:\n{raw}')

        songs = []
        try:
            if info['tracks'][0]['is_playable'] == True:

                thumbnail = info['tracks'][0]['album']['images'][0]
                for i in info['tracks'][0]['album']['images']:
                    if i['width'] is not None:
                        if i['width'] > thumbnail['width']:
                            thumbnail = i
                    else:
                        pass
                
                songs.append({
                    'track_platform': 'spotify',
                    'title': info['tracks'][0]['name'],
                    'track_type': info['tracks'][0]['type'],
                    'track_id': info['tracks'][0]['id'],
                    'is_playable': info['tracks'][0]['is_playable'],
                    'duration': round(int(info['tracks'][0]['duration_ms']) / 1000),
                    'track_url': info['tracks'][0]['external_urls']['spotify'],
                    'image': thumbnail,
                    'thumbnail_url': thumbnail['url']
                })
            else:
                pass
            return songs
        except Exception as e:
            raise ValueError(f'Failed to parse TRACKS_URL response: {str(e)}\n{raw}')

    def get_playlist_info(self, playlist_id):
        """ returns a dictionary of playlist info + list of songs (0-100) """

        (raw, resp) = self.invoke_url(f'{PLAYLISTS_URL}/{playlist_id}?fields=name,tracks,external_urls\
        ,images,type,uri,public&market=from_token')

        playlist_data = {
            'title': resp['name'],
            'url': 'https://open.spotify.com/playlist/'+str(playlist_id),
            'id': playlist_id,
            'type': resp['type'],
            'public': resp['public'],
            'image': resp['images'][0]
        }
        for i in resp['images']:
            if i['width'] is not None:
                if i['width'] > playlist_data['image']['width']:
                    playlist_data['image'] = i
                else:
                    pass
        playlist_data['thumbnail_url'] = playlist_data['image']['url']

        if resp['tracks']['items'] == []:
            songs = []
        else:
            songs = []
            for item in resp['tracks']['items']:
                if item['track']['is_playable'] == True:
                    
                    thumbnail = item['track']['album']['images'][0]
                    for i in item['track']['album']['images']:
                        if i['width'] is not None:
                            if i['width'] > thumbnail['width']:
                                thumbnail = i
                        else:
                            pass

                    songs.append({
                        'track_platform': 'spotify',
                        'title': item['track']['name'],
                        'track_type': item['track']['type'],
                        'track_id': item['track']['id'],
                        'is_playable': item['track']['is_playable'],
                        'track_url': item['track']['external_urls']['spotify'],
                        'duration': round(int(item['track']['duration_ms']) / 1000),
                        'image': thumbnail,
                        'thumbnail_url': thumbnail['url']
                    })
                else:
                    continue
        playlist_data['playlist_items'] = songs
        return playlist_data

    def get_album_info(self, album_id):
            """ returns a dictionary of album info + list of songs (0-50) """

            (raw, resp) = self.invoke_url(f'{ALBUM_URL}/{album_id}')
            
            album_data = {
                'title': resp['name'],
                'url': resp['external_urls']['spotify'],
                'id': resp['id'],
                'type': resp['type'],
                'image': resp['images'][0]
            }
            for i in resp['images']:
                if i['width'] is not None:
                    if i['width'] > album_data['image']['width']:
                        album_data['image'] = i
                else:
                    pass
            album_data['thumbnail_url'] = album_data['image']['url']

            if resp['tracks']['items'] == []:
                songs = []
            else:
                songs = []
                for item in resp['tracks']['items']:
                    songs.append({
                        'track_platform': 'spotify',
                        'title': item['name'],
                        'track_type': item['type'],
                        'track_id': item['id'],
                        'is_playable': True,
                        'track_url': item['external_urls']['spotify'],
                        'duration': round(int(item['duration_ms']) / 1000),
                        'image': album_data['image'],
                        'thumbnail_url': album_data['thumbnail_url']
                    })
            album_data['album_items'] = songs
            return album_data


    def download_track(self, track_id, guild_id, downloadDirectory):
        """ Downloads raw song audio from Spotify """
        retry_counts = 0
        guild_id = str(guild_id)
        download_dir = str(downloadDirectory)
        filename = f"{track_id}.{guild_id}.{self.extension}"
        location = f"{download_dir}/{filename}"

        while retry_counts < MAX_RETRIES:
            try:
                track = TrackId.from_base62(track_id)
                stream = self.get_content_stream(track, self.quality)
                total_size = stream.input_stream.size

                downloaded = 0
                with open(location, 'wb') as file:
                    b = 0
                    while b < 5:
                        data = stream.input_stream.stream().read(DATA_CHUNK_SIZE)
                        downloaded += len(data)
                        b += 1 if data == b'' else 0
                        file.write(data)

                print("Download Successful.")
                # self.convert_audio_format(filename, location, f"{download_dir}/ready")
                return
            except Exception as e:
                print("error encountered",e)
                retry_counts += 1
                print("Retrying ...",retry_counts)
                time.sleep(1)
        else:
            print(f"Failed to download this track after {MAX_RETRIES} attempts. Skipping...")
            retry_counts = 0

    def convert_audio_format(self, filename, dl_location, final_location):
        """ Converts raw audio into playable file """
        print("Converting Audio...")
        out_ = f"{final_location}/{filename}.{self.extension}"

        output_params = ['-c:a', self.codec]
        if self.bitrate:
            output_params += ['-b:a', self.bitrate]

        try:
            ff_m = ffmpy.FFmpeg(
                global_options=['-y', '-hide_banner', '-loglevel error'],
                inputs={dl_location: None},
                outputs={out_: output_params}
            )
            ff_m.run()
            print("Done")
        except ffmpy.FFExecutableNotFoundError:
            print(f'FFMPEG NOT FOUND   ###')