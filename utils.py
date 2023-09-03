import os
import re
import yaml
import json
import glob
import signal
import yt_dlp
from urllib import parse, request

from spotify.client import Client
from spotify.const import CREDENTIAL_LOCATION
from spotify.const import DOWNLOAD_DIR


class Config():
	def __init__(self):
		with open('config.yml', 'r') as file:
			data = yaml.safe_load(file)
		self.BOT_TOKEN = data['DISCORD']['BOT_TOKEN']
		self.DOWNLOAD_DIR = "rds" # No "/" at the end.
		self.spotify = data['DISCORD']['SPOTIFY_SUPPORT']
		if self.spotify == True:
			self.spotify_username = data['SPOTIFY']['USERNAME']
			self.spotify_password = data['SPOTIFY']['PASSWORD']
	
	def setupSpotifyClient(self):
		try:
			if self.spotify_username == "" or self.spotify_password == "":
				print("Please provide spotify credentials.")
				exit()
			else:
				global spClient 
				spClient = Client()
				spClient.login(CREDENTIAL_LOCATION, self.spotify_username, self.spotify_password)
		except Exception as e:
			print(f"Unable to setup spotify client, reason: {e}")


def getDuration(seconds):
	seconds = int(seconds)
	m, s = divmod(seconds, 60)
	if seconds >= 3600:
		h, m = divmod(m, 60)
		track_length = f"{h:d}:{m:02d}:{s:02d}"
		return track_length
	else:
		track_length = f"{m:02d}:{s:02d}"
		return track_length


def search(queryString, platform):
	if platform == 'youtube':
		print(queryString)
		searchString = parse.urlencode({'search_query': queryString})
		print(searchString)
		htmContent = request.urlopen(
			'http://www.youtube.com/results?' + searchString)
		searchResults = re.findall(
			'/watch\?v=(.{11})', htmContent.read().decode())

		return {
			'platform': 'youtube',
			'type': 'single_track',
			'id': searchResults[1],
			'url': "https://www.youtube.com/watch?v="+searchResults[1],
			'error': None
		}
	else:
		return {
			'error': 'platform_unsupported',
			'message': 'The requested platform is not supported for searching tracks.'
		}


def parse_args(query):
	query = str(query)
	if query == "" or query == " ":
		return  {
			'error': 'no_argument_passed',
			'message': 'Please enter a song link or name.'
		}
	else:
		pass

	parse = {}

	album_uri_search = re.search(
		r'^spotify:album:(?P<AlbumID>[0-9a-zA-Z]{22})$', query)
	album_url_search = re.search(
		r'^(https?://)?open\.spotify\.com/album/(?P<AlbumID>[0-9a-zA-Z]{22})(\?(si|highlight)=.+?)?$',
		query,
	)

	playlist_uri_search = re.search(
		r'^spotify:playlist:(?P<PlaylistID>[0-9a-zA-Z]{22})$', query)
	playlist_url_search = re.search(
		r'^(https?://)?open\.spotify\.com/playlist/(?P<PlaylistID>[0-9a-zA-Z]{22})(\?(si|highlight)=.+?)?$',
		query,
	)

	track_uri_search = re.search(
		r'^spotify:track:(?P<TrackID>[0-9a-zA-Z]{22})$',query)
	track_url_search = re.search(
		r'^(https?://)?open\.spotify\.com/track/(?P<TrackID>[0-9a-zA-Z]{22})(\?(si|highlight)=.+?)?$',
		query,
	)

	youtube_search = re.search(
		r'^((?:https?:)?\/\/)?((?:www|m)\.)?(?:youtube\.com|youtu.be)(\/(?:[\w\-]+\?v=|embed\/|v\/)?)(?P<video_id>[\w\-]+)(\S+)?$',
		query,
	)

	youtube_music_search = re.search(
		r'^(?:https?:\/\/)?(?:www\.)?(?:music\.)?youtube\.com\/(?:watch\?(?=.*v=)(?:[\w\-]+=[\w\-]+&)*v=|v\/|embed\/)?(?P<video_id>[\w\-]+)(?:\S+)?$',
		query,
	)

	if album_uri_search is not None or album_url_search is not None:
		parse['platform'] = 'spotify'
		parse['type'] = 'album'
		parse['id'] = (album_uri_search.group("AlbumID") if album_uri_search is not None else 
						album_url_search.group("AlbumID"))
		parse['url'] = query
		parse['error'] = None
		return parse

	if playlist_uri_search is not None or playlist_url_search is not None:
		parse['platform'] = 'spotify'
		parse['type'] = 'playlist'
		parse['id'] = (playlist_uri_search.group("PlaylistID") if playlist_uri_search is not None else 
						playlist_url_search.group("PlaylistID"))
		parse['url'] = query
		parse['error'] = None
		return parse

	if track_uri_search is not None or track_url_search is not None:
		parse['platform'] = 'spotify'
		parse['type'] = 'single_track'
		parse['id'] = (track_uri_search.group("TrackID") if track_uri_search is not None else
						track_url_search.group("TrackID"))
		parse['url'] = query
		parse['error'] = None
		return parse
	
	if youtube_music_search is not None or youtube_search is not None:
		parse['platform'] = ('youtube' if youtube_search is not None else
							'youtube_music')
		parse['type'] = 'single_track'
		parse['id'] = (youtube_music_search.group("video_id") if youtube_music_search is not None else
						youtube_search.group("video_id"))
		parse['url'] = query
		parse['error'] = None
		print(parse)
		return parse

	if "http://" in query or "https://" in query:
		return {
			'error': 'unsupported_link',
			'message': 'Unknown link provided. please type `/help` for usage.'
		}

	else:
		return search(query, 'youtube')



def getTrack(track_bundle):

	YT_EXT_OPTIONS = {
			"format": "bestaudio",
			"no-playlist": True,
	}

	if track_bundle['platform'] == 'spotify':
		if track_bundle['type'] == 'single_track':
			return {
				'bundle_type': 'single_track',
				'platform': 'spotify',
				'songs': spClient.get_song_info(track_bundle['id']),
			}
		elif track_bundle['type'] == 'playlist':
			return {
				'bundle_type': 'playlist_info',
				'platform': 'spotify',
				'playlist_data': spClient.get_playlist_info(track_bundle['id']),
			}
		else:
			return {
				'bundle_type': 'album_info',
				'platform': 'spotify',
				'album_data': spClient.get_album_info(track_bundle['id']),
			}

	if track_bundle['platform'] == 'youtube_music':
		url = "https://music.youtube.com/watch?v="+str(track_bundle['id'])

		with yt_dlp.YoutubeDL(YT_EXT_OPTIONS) as ydl:
			try:
				info = ydl.extract_info(url, download=False)
			except Exception as e:
				print(f"Error extracting video info, link: {url}\n {e}")
		return {
			'bundle_type': 'single_track',
			'platform': 'youtube_music',
			'songs': [{
				'track_platform': 'youtube_music',
				'title': info['title'],
				'track_type': 'track',
				'track_id': str(track_bundle['id']),
				'is_playable': True,
				'duration': info['duration'],
				'track_url': url,
				'thumbnail_url': 'https://i.ytimg.com/vi/'+str(track_bundle['id'])+'/hqdefault.jpg',
			}],
		}		
		
	else:
		url = "https://www.youtube.com/watch?v="+str(track_bundle['id'])

		with yt_dlp.YoutubeDL(YT_EXT_OPTIONS) as ydl:
			try:
				info = ydl.extract_info(url, download=False)
			except Exception as e:
				print(f"Error extracting video info, link: {url}\n {e}")
		return {
			'bundle_type': 'single_track',
			'platform': 'youtube',
			'songs': [{
				'track_platform': 'youtube',
				'title': info['title'],
				'track_type': 'track',
				'track_id': str(track_bundle['id']),
				'is_playable': True,
				'duration': info['duration'],
				'track_url': url,
				'thumbnail_url': 'https://i.ytimg.com/vi/'+str(track_bundle['id'])+'/hqdefault.jpg',
			}],
		}



def downloadTrack(trackBundle, guild_id, downloadDirectory):

	guild_id = str(guild_id)
	downloadDirectory = str(downloadDirectory)

	YT_DL_OPTIONS = {
				"format": "bestaudio",
				"no-playlist": True,
				# "outtmpl": "rds/"+track_id+"."+id+".%(ext)s",
	}

	if trackBundle['track_platform'] == 'youtube':
		YT_DL_OPTIONS["outtmpl"] = f"{downloadDirectory}/{trackBundle['track_id']}.{guild_id}.%(ext)s"
		url = "https://www.youtube.com/watch?v="+str(trackBundle['track_id'])
		with yt_dlp.YoutubeDL(YT_DL_OPTIONS) as ydl:
			ydl.download(url)

	if trackBundle['track_platform'] == 'youtube_music':
		YT_DL_OPTIONS["outtmpl"] = f"{downloadDirectory}/{trackBundle['track_id']}.{guild_id}.%(ext)s"
		url = "https://music.youtube.com/watch?v="+str(trackBundle['track_id'])
		with yt_dlp.YoutubeDL(YT_DL_OPTIONS) as ydl:
			ydl.download(url)
	
	if trackBundle['track_platform'] == 'spotify':
		loc = spClient.download_track(trackBundle['track_id'], guild_id, downloadDirectory)

	loc = glob.glob(f"{downloadDirectory}/{trackBundle['track_id']}.{guild_id}.*")
	if loc == []:
		return None
	return loc[0]



def deleteTrack(guild_id, downloadDirectory):
	# for file in os.listdir("./rds"):
	# 	if file.endswith(f"{id}.webm"):
	for file in glob.glob(f"{downloadDirectory}/*.{str(guild_id)}.*"):
		if os.path.exists(file) is True:
			os.remove(file)
			print(f"File Deleted: {file}")



def kill_process(pid):
	print(f"Killing Process: {str(pid)}")
	os.kill(pid, signal.SIGTERM)
	return