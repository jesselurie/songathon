# -*- coding: utf-8 -*-
import os
import soundcloud
import requests
import urllib
import json
import re
import shutil
from pydub import AudioSegment
from flask import Flask
from subprocess import call
from time import sleep
from docker import Client
from io import BytesIO

class Genice():
	def __init__(self,username,port):
		self.username = str(username)
		self.path = str("/home/"+self.username+"/")
		self.port=str(port)
		self.mp3path="/home/"+self.username+"/mp3/"
		self.base_url = "https://soundcloud.com"
		self.client = soundcloud.Client(client_id="8fe8a9caa3e7ade8b6dba5c9d21b3549")
		try:
			shutil.rmtree(self.path)	
		except Exception as E:
			pass
					
		try:
			os.mkdir(self.path,777)
		except Exception as E:
			pass

		try:
			os.mkdir(self.mp3path,777)
		except Exception as E:
			pass
			#shutil.rmtree(self.mp3path)			
			


	def gen_files(self):
		dockerfilepath = str(self.path+"Dockerfile")
		configtxtpath = str(self.path+"config.txt")
		icecastxmlpath = str(self.path+"icecast.xml")

		dockerfile = ('''FROM moul/icecast
		ADD /icecast.xml /etc/icecast2/
		#ENV VIRTUAL_HOST '''+self.username+'''.159.203.93.163
		#add the default song for user to not have to use icegenerator
		''')

		configtxt = str(('''NAME='''+self.username+'''\nIP=159.203.93.163\nPORT='''+self.port+'''\n# 2 – Icecast 2.0 (HTTP protocol compatible)\nSERVER=2\nSOURCE=source\nPASSWORD=coeval1234567\nFORMAT=1\nRECURSIVE=1\nDUMPFILE=\nLOOP=0\nSHUFFLE=1\nBITRATE=48000\nPUBLIC=0\nMETAUPDATE=5\nMDFPATH=/root/icegenerator/global.mdf\nLOG=2\nLOGPATH=/root/icegenerator/icegenerator.log\nDATAPORT=8796\n#######################################################\nMOUNT=/'''+self.username+'''\nMP3PATH=pth:/'''+self.mp3path+'''\nGENRE=Type of Music\nDESCRIPTION=Radio Description\nURL=http://www.songathon.xyz:'''+self.port+'''/'''+self.username+''''''))

		icecastxml =str(('''
		<icecast>
		    <limits>
		        <clients>100</clients>
		        <sources>100</sources>
		        <threadpool>5</threadpool>
		        <queue-size>524288</queue-size>
		        <client-timeout>30</client-timeout>
		        <header-timeout>15</header-timeout>
		        <source-timeout>10</source-timeout>
		        <!-- If enabled, this will provide a burst of data when a client 
		             first connects, thereby significantly reducing the startup 
		             time for listeners that do substantial buffering. However,
		             it also significantly increases latency between the source
		             client and listening client.  For low-latency setups, you
		             might want to disable this. -->
		        <burst-on-connect>1</burst-on-connect>
		        <!-- same as burst-on-connect, but this allows for being more
		             specific on how much to burst. Most people won't need to
		             change from the default 64k. Applies to all mountpoints  -->
		        <burst-size>65535</burst-size>
		    </limits>

		    <authentication>
		        <!-- Sources log in with username 'source' -->
		        <source-password>coeval1234567</source-password>
		        <!-- Relays log in username 'relay' -->
		        <relay-password>coeval</relay-password>

		        <!-- Admin logs in with the username given below -->
		        <admin-user>admin</admin-user>
		        <admin-password>coeval</admin-password>
		    </authentication>

		       <!-- set the mountpoint for a shoutcast source to use, the default if not
		         specified is /stream but you can change it here if an alternative is
		         wanted or an extension is required -->
		    <shoutcast-mount>/'''+self.username+'''.mp3</shoutcast-mount>

		    <!-- Uncomment this if you want directory listings -->
		    <!--
		    <directory>
		        <yp-url-timeout>15</yp-url-timeout>
		        <yp-url>http://dir.xiph.org/cgi-bin/yp-cgi</yp-url>
		    </directory>
		     -->

		    <!-- This is the hostname other people will use to connect to your server.
		    It affects mainly the urls generated by Icecast for playlists and yp
		    listings. -->
		    <hostname>rica</hostname>

		    <!-- You may have multiple <listener> elements -->
		    <listen-socket>
		        <port>'''+self.port+'''</port>
		      <!--  <bind-address>159.203.93.163</bind-address> 
		         <shoutcast-mount>/radiostream</shoutcast-mount> -->
		    </listen-socket>
		    <!--
		    <listen-socket>
		        <port>8001</port>
		    </listen-socket>
		    -->

		    <!--<master-server>127.0.0.1</master-server>-->
		    <!--<master-server-port>8001</master-server-port>-->
		    <!--<master-update-interval>120</master-update-interval>-->
		    <!--<master-password>hackme</master-password>-->

		    <!-- setting this makes all relays on-demand unless overridden, this is
		         useful for master relays which do not have <relay> definitions here.
		         The default is 0 -->
		    <!--<relays-on-demand>1</relays-on-demand>-->

		    <!--
		    <relay>
		        <server>127.0.0.1</server>
		        <port>8001</port>
		        <mount>/example.ogg</mount>
		        <local-mount>/different.ogg</local-mount>
		        <on-demand>0</on-demand>

		        <relay-shoutcast-metadata>0</relay-shoutcast-metadata>
		    </relay>
		    -->

		    <!-- Only define a <mount> section if you want to use advanced options,
		         like alternative usernames or passwords
		    <mount>
		        <mount-name>/example-complex.ogg</mount-name>

		        <username>othersource</username>
		        <password>hackmemore</password>

		        <max-listeners>1</max-listeners>
		        <dump-file>/tmp/dump-example1.ogg</dump-file>
		        <burst-size>65536</burst-size>
		        <fallback-mount>/example2.ogg</fallback-mount>
		        <fallback-override>1</fallback-override>
		        <fallback-when-full>1</fallback-when-full>
		        <intro>/example_intro.ogg</intro>
		        <hidden>1</hidden>
		        <no-yp>1</no-yp>
		        <authentication type="htpasswd">
		                <option name="filename" value="myauth"/>
		                <option name="allow_duplicate_users" value="0"/>
		        </authentication>
		        <on-connect>/home/icecast/bin/stream-start</on-connect>
		        <on-disconnect>/home/icecast/bin/stream-stop</on-disconnect>
		    </mount>

		    <mount>
		        <mount-name>/auth_example.ogg</mount-name>
		        <authentication type="url">
		            <option name="mount_add"       value="http://myauthserver.net/notify_mount.php"/>
		            <option name="mount_remove"    value="http://myauthserver.net/notify_mount.php"/>
		            <option name="listener_add"    value="http://myauthserver.net/notify_listener.php"/>
		            <option name="listener_remove" value="http://myauthserver.net/notify_listener.php"/>
		        </authentication>
		    </mount>

		    -->

		    <fileserve>1</fileserve>

		    <paths>
				<!-- basedir is only used if chroot is enabled -->
		        <basedir>/usr/share/icecast2</basedir>

		        <!-- Note that if <chroot> is turned on below, these paths must both
		             be relative to the new root, not the original root -->
		        <logdir>/var/log/icecast2</logdir>
		        <webroot>/usr/share/icecast2/web</webroot>
		        <adminroot>/usr/share/icecast2/admin</adminroot>
		        <!-- <pidfile>/usr/share/icecast2/icecast.pid</pidfile> -->

		        <!-- Aliases: treat requests for 'source' path as being for 'dest' path
		             May be made specific to a port or bound address using the "port"
		             and "bind-address" attributes.
		          -->
		        <!--
		        <alias source="/foo" dest="/bar"/>
		          -->
		        <!-- Aliases: can also be used for simple redirections as well,
		             this example will redirect all requests for http://server:port/ to
		             the status page
		          -->
		        <alias source="/" dest="/status.xsl"/>
		    </paths>

		    <logging>
		        <accesslog>access.log</accesslog>
		        <errorlog>error.log</errorlog>
		        <!-- <playlistlog>playlist.log</playlistlog> -->
		      	<loglevel>3</loglevel> <!-- 4 Debug, 3 Info, 2 Warn, 1 Error -->
		      	<logsize>10000</logsize> <!-- Max size of a logfile -->
		        <!-- If logarchive is enabled (1), then when logsize is reached
		             the logfile will be moved to [error|access|playlist].log.DATESTAMP,
		             otherwise it will be moved to [error|access|playlist].log.old.
		             Default is non-archive mode (i.e. overwrite)
		        -->
		        <!-- <logarchive>1</logarchive> -->
		    </logging>

		    <security>
		        <chroot>0</chroot>
		        <!--
		        <changeowner>
		            <user>nobody</user>
		            <group>nogroup</group>
		        </changeowner>
		        -->
		    </security>
		</icecast>
		'''))

		wdock = open(dockerfilepath,'w')
		wdock.write(dockerfile)
		wdock.close()
		wdock = open(configtxtpath,'w')
		wdock.write(configtxt)
		wdock.close()
		wdock = open(icecastxmlpath,'w')
		wdock.write(icecastxml)
		wdock.close()

	def gen_container(self):
		ports=str(self.port+":"+self.port)
		call(["docker","build","-t",self.username+"/icecast",self.path])
		call(["docker","run","-d","-p",ports,self.username+"/icecast"])
		sleep(3)
		call(["icegenerator","-f","/home/"+self.username+"/config.txt"])
		
	def gen_stream(self):
		call(["icegenerator","-f","/home/"+self.username+"/config.txt"])

	def get_songs(self,q):
		#songs = requests.get("http://api.soundcloud.com/tracks?client_id=8fe8a9caa3e7ade8b6dba5c9d21b3549&?title="+q)
		songs = requests.get("http://api.soundcloud.com/tracks?q="+q+"?&client_id=8fe8a9caa3e7ade8b6dba5c9d21b3549&limit=3&format=json&_status_code_map%5B302%5D=200")
		#songs = requests.get("http://api.soundcloud.com/tracks?client_id=8fe8a9caa3e7ade8b6dba5c9d21b3549&?title="+q+"&?lable_name="+q+"&?tags="+q+"&?ids="+q+"&?limit=20")
		songs = json.loads(songs.text)
		thesongs = []
		for i in songs:
			if songs['stream_url']:
				thesongs.append(i)
		#only return songs with stream_url as true
		return thesongs

	def get_song(self,songid):
		songs = requests.get("http://api.soundcloud.com/tracks/"+songid+"?client_id=8fe8a9caa3e7ade8b6dba5c9d21b3549")
		songs = json.loads(songs.text)
		#get stream url
		stream_url = self.client.get(songs["stream_url"], allow_redirects=False)
		#download soundcloud to mp3 with songid as name
		songid = str(songid+".mp3")
		song = urllib.urlretrieve(stream_url.location, songid)
		os.rename("/var/www/coeval/coeval/"+songid, "/home/"+self.username+"/mp3/"+songid)



# x = Genice("lauren","8004")
# tg = str(username+'/icecast')
# f = BytesIO(dockerfile.encode('utf-8'))
# c = Client(base_url='unix://var/run/docker.sock')
# c.build(path='/home/'+username+'/', rm=True, tag=username+'/icecast')
# container = c.create_container(image=tg, ports=[8000,8000])
# c.start(container[u'Id'],port_bindings={8000:8000})
# call(["icegenerator", "-f","/home/"+username+"/config.txt"])
# subprocess.call("icegenerator",['-f','/home/'+username+'/config.txt'],shell=False)
# c.stop(container[u'Id'],timeout=10)
# c.remove_container(container[u'Id'],v=False,link=False)
