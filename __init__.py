import json
import soundcloud_cli
from flask import Flask,jsonify,url_for, render_template,request,redirect
from genice import *

# username = "juanfer"
# port = "8004"
app = Flask(__name__)
sound = soundcloud_cli.Soundc()
#test
#/var/www/coeval/coeval
#python __init__.py

# @app.route('/',methods=['POST','GET'])
# def index():
# 	if request.method == "POST":
# 		songs = x.get_songs(str(request.form['term']))
# 		return render_template('songs.html',songs=songs)
# 	return render_template('index.html')

# @app.route('/stream',methods=['POST','GET'])
# def stream():
# 	if request.method =="POST":
# 		songs = x.get_song(str(request.form['songid']))
# 		x.gen_files()
# 		x.gen_stream()
# 		x.gen_container()
# 		return redirect("http://www.songathon.xyz:"+port+"/"+username, code=302)
# 	return render_template('stream.html')

@app.route('/api/<username>/<port>/<song>',methods=['POST','GET'])
def search(username,port,song):
	x = Genice(str(username),str(port))
	songs = x.get_songs(str(song))
	songs = x.get_song(str(songs[0]["id"]))
	x.gen_files()	
	x.gen_container()
	#return redirect("159.203.93.163:"+port+"/"+username, code=302)
	return jsonify({"done":songs})

@app.route('/api/username/port/<songid>',methods=['POST','GET'])
def searchid(username,port,songid):
	x = Genice(str(username),str(port))
	song = x.get_song(str(songid))
	x.gen_files()
	x.gen_container()
	return jsonify({"song":song})

# @app.route('/api/container/<username>/<port>',methods=['POST','GET'])
# def init(username,port):
# 	x = Genice(username=username,port=port)
# 	x.gen_files()
# 	x.gen_container()
# 	return jsonify({"done":"done"})

if __name__ == "__main__":
	app.run(debug=True,host='159.203.93.163',port=5000)

