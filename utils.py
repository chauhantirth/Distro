import os
import re
import json
import signal
import yt_dlp
from urllib import parse, request

def checkArgs(query):
	track = {}

	if query == '':
		track['error'] = 'empty_string'
		return track
	
	elif 'https://open.spotify.com' in query:
		track['error'] = 'url_unsupported'
		return track

	elif '&list' in query:
		urlSplit = query.split("&list")
		url = urlSplit[0]
		urlSplit = url.split("?v=")
		track_id = urlSplit[1]
		url_type = 'yt_playlist_track'
	
	elif 'youtu.be' in query:
		urlSplit = query.split("be/")
		url = "https://www.youtube.com/watch?v="+urlSplit[1]
		track_id = urlSplit[1]
		url_type = 'yt_single_track'
	
	elif 'watch?v=' in query:
		urlSplit = query.split("?v=")
		track_id = urlSplit[1]
		url = "https://www.youtube.com/watch?v="+urlSplit[1]
		url_type = 'yt_single_track'
	
	else:
		print("Searching Track")
		searchString = parse.urlencode({'search_query': query})
		htmContent = request.urlopen(
			'http://www.youtube.com/results?' + searchString)
		searchResults = re.findall(
            '/watch\?v=(.{11})', htmContent.read().decode())

		track['error'] = ''
		track['url'] = "https://www.youtube.com/watch?v="+searchResults[0]
		track['id'] = searchResults[0]
		track['url_type'] = 'yt_single_track'

		return track


	track['error'] = ''
	track['url'] = url
	track['id'] = track_id
	track['url_type'] =	url_type

	return track

def getTrack(track_id):

	url = "https://www.youtube.com/watch?v="+track_id
	
	YT_EXT_OPTIONS = {
				"format": "bestaudio",
				"no-playlist": True,
	}
	
	with yt_dlp.YoutubeDL(YT_EXT_OPTIONS) as ydl:
		try:
			info = ydl.extract_info(url, download=False)
		except:
			return False
	
	trackData = {
		'id': track_id,
		'title': info['title'],
		'url': url,
		'thumbnail': 'https://i.ytimg.com/vi/' + track_id + '/hqdefault.jpg',
		'duration': info['duration'],
		'platform': 'youtube'
	}
	
	return trackData

def downloadTrack(track_id, id):

	url = "https://www.youtube.com/watch?v="+track_id

	YT_DL_OPTIONS = {
				"format": "bestaudio",
				"no-playlist": True,
				"outtmpl": "rds/"+track_id+"."+id+".%(ext)s",
	}

	with yt_dlp.YoutubeDL(YT_DL_OPTIONS) as ydl:
		ydl.download(url)


def deleteTrack(id):
	for file in os.listdir("./rds"):
		if file.endswith(f"{id}.webm"):
			os.remove("rds/"+file)
			print(f"File Deleted: {file}")


def kill_process(pid):
	os.kill(pid, signal.SIGTERM)
	return