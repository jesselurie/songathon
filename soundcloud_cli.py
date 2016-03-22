import soundcloud
import requests
import audioread
import urllib
import json
import re
from pydub import AudioSegment
#159.203.93.163

class Soundc():
	def __init__(self):
		self.href = re.compile("href")
		self.base_url = "https://soundcloud.com"
		self.client = soundcloud.Client(client_id="8fe8a9caa3e7ade8b6dba5c9d21b3549")


	def get_songs(self,q):
		#songs = requests.get("http://api.soundcloud.com/tracks?client_id=8fe8a9caa3e7ade8b6dba5c9d21b3549&?title="+q)
		songs = requests.get("http://api.soundcloud.com/tracks?q="+q+"?&client_id=8fe8a9caa3e7ade8b6dba5c9d21b3549&limit=10&format=json&_status_code_map%5B302%5D=200")
		#songs = requests.get("http://api.soundcloud.com/tracks?client_id=8fe8a9caa3e7ade8b6dba5c9d21b3549&?title="+q+"&?lable_name="+q+"&?tags="+q+"&?ids="+q+"&?limit=20")
		songs = json.loads(songs.text)
		thesongs = []
		for i in songs:
			if i['streamable'] == True:
				thesongs.append(i)
		return thesongs

	def get_song(self,songid):
		songs = requests.get("http://api.soundcloud.com/tracks/"+songid+"?client_id=8fe8a9caa3e7ade8b6dba5c9d21b3549")
		songs = json.loads(songs.text)
		#get stream url
		stream_url = self.client.get(songs["stream_url"], allow_redirects=False)
		#download soundcloud to mp3 with songid as name
		song = urllib.urlretrieve(stream_url.location, str(songid+".mp3"))
		return songs




