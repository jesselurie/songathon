
async_mode = None

if async_mode is None:
    try:
        import eventlet
        async_mode = 'eventlet'
    except ImportError:
        pass

    if async_mode is None:
        try:
            from gevent import monkey
            async_mode = 'gevent'
        except ImportError:
            pass

    if async_mode is None:
        async_mode = 'threading'

    print('async_mode is ' + async_mode)

# monkey patching is necessary because this application uses a background
# thread
if async_mode == 'eventlet':
    import eventlet
    eventlet.monkey_patch()
elif async_mode == 'gevent':
    from gevent import monkey
    monkey.patch_all()

import time
from threading import Thread
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect

import json
import requests
import soundcloud_cli
from flask import Flask,jsonify,url_for,render_template,request,redirect,session
from flask.ext.pymongo import PyMongo
from genice import *
from docker import Client
from subprocess import call
from bson.json_util import dumps


cli_doc = Client(base_url='unix://var/run/docker.sock')
cli = soundcloud_cli.Soundc()

app = Flask(__name__)
app.secret_key = '/x01/as/os/$#q\wert!/qx0'  # Change this!
app.config['config_prefix']='MONGO'
app.config['MONGO_HOST'] ='songathon.xyz'
#users exitst now using users_test for testing
#drop all dbs
app.config['MONGO_DBNAME'] = 'users_test'
app.config['MONGO_PORT'] = 27017
mongo = PyMongo(app,config_prefix='MONGO')

app.config['config_prefix']='MONGO2'
app.config['MONGO2_HOST'] ='songathon.xyz'
app.config['MONGO2_DBNAME'] = 'ports'
app.config['MONGO2_PORT'] = 27017
mongo_port = PyMongo(app,config_prefix='MONGO2')

socketio = SocketIO(app, async_mode=async_mode)
thread = None

@socketio.on('my event', namespace='/test')
def test_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': message['data'], 'count': session['receive_count']})


@socketio.on('my broadcast event', namespace='/test')
def test_broadcast_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': message['data'], 'count': session['receive_count']},
         broadcast=True)


@socketio.on('join', namespace='/test')
def join(message):
    join_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})


@socketio.on('leave', namespace='/test')
def leave(message):
    leave_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})


@socketio.on('close room', namespace='/test')
def close(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response', {'data': 'Room ' + message['room'] + ' is closing.',
                         'count': session['receive_count']},
         room=message['room'])
    close_room(message['room'])


@socketio.on('my room event', namespace='/test')
def send_room_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': message['data'], 'count': session['receive_count']},
         room=message['room'])


@socketio.on('disconnect request', namespace='/test')
def disconnect_request():
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': 'Disconnected!', 'count': session['receive_count']})
    disconnect()


@socketio.on('connect', namespace='/test')
def test_connect():
    emit('my response', {'data': '', 'count': 0})


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected', request.sid)

import flask.ext.login as flask_login
from flask.ext.login import current_user

login_manager = flask_login.LoginManager()
login_manager.init_app(app)

class User(flask_login.UserMixin):
    pass

@login_manager.user_loader
def user_loader(email):
	userr = mongo.db.users.find_one({'username':email})
	if not userr:
		return
	user = User()
	user.id = userr['username']
	return user

@login_manager.request_loader
def request_loader(request):
	username = request.form.get('username')
	userr = mongo.db.users.find_one({'username':username})
	if not userr:
		return
	user = User()
	user.id = username
	# DO NOT ever store passwords in plaintext and always compare password
	# hashes using constant-time comparison!
	user.is_authenticated = request.form['pw'] == userr['password']
	return user

@login_manager.unauthorized_handler
def unauthorized_handler():
	#unauthorized landing page
    return 'Unauthorized'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    username = request.form['username']
    user = mongo.db.users.find_one({'username':username})
    try:
		if request.form['pw'] == user['password']:
		    user = User()
		    user.id = username
		    flask_login.login_user(user)
		    return redirect(url_for('index'))
    except Exception as e:
    	pass
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
	#mongo.db.users.update_one({'username':str(current_user.id)},{'$set': {'streaming':False}})
	flask_login.logout_user()
	return redirect(url_for('login'))


@app.route('/search',methods=['POST','GET'])
@flask_login.login_required
def index():
	#query db to return a list of users urls streaming attribute is true
	#return list of user urls for buttons
	#loop through and when visitor clicks button it redurects to url on button
	#mongo.db.users.update_one({'username':str(current_user.id)},{'$set': {'streaming':False}})
	#check is user has continer and destroy it
	if request.method == "POST":
		search = str(request.form['term'])
		songs = cli.get_songs(search)
		return render_template('songs.html',songs=songs)
	return render_template('index.html')

@app.route('/play',methods=['POST','GET'])
@flask_login.login_required
def play():
	theuser = mongo.db.users.find_one({'username':str(flask_login.current_user.id)})
	streaming_users = mongo.db.users.find({'streaming':True})
	if request.method == "POST":
		songid = request.form['songid']
		#change these params for the mongo db
		#erase existing directories for users before creating and downloading mp3
		#fix the porting issue
		#kill -9 `fuser -n tcp 8010`
		call(["kill","-9","-t",'fuser -n tcp'+str(theuser['port'])])
		x = Genice(str(theuser['username']),str(theuser['port']))
		song = x.get_song(songid) 
		x.gen_files()
		x.gen_container()
		#update streaming attribute to True 
		mongo.db.users.update_one({'username':str(current_user.id)},{'$set': {'streaming':True}})
		#find all streaming users
		#streaming_users = mongo.db.users.find({'streaming':True})
		#find all the urls associated with the streaming users
		return render_template('streaming.html',url=theuser['url'],username=theuser['username'])
		#return render_template('play.html',song=song)
	return render_template('stream.html',streaming_users=streaming_users)

@app.route('/',methods=['POST','GET'])
def stream():
	#when restarting database inseter one initial value for ports to 8000
	#query db and find all users that streming attribute is True
	#mongo.db.users.update_one({'username':str(current_user.id)},{'$set': {'streaming':False}})
	streaming_users = mongo.db.users.find({'streaming':True})
	return render_template('stream.html',streaming_users=streaming_users)

@app.route('/turnup',methods=['POST','GET'])
def turnup():
	#template this so the url is the username
	url=request.form['url']
	username=request.form['username']
	return render_template('chat.html',url=url,username=username)
	#return render_template('streaming.html')


@app.route('/register',methods=['POST','GET'])
def register():
	print cli_doc.containers()
	if request.method == "POST":
		username = request.form['username']
		email = request.form['email']
		password = request.form['pw']
		confpassword = request.form['cpw']	
		result = mongo.db.users.find_one({'username':username})
		if result:
			#if username in register is true print "username is already in user" on register.html
			return render_template('register.html',user=username)
		else:
			#insert new user here
			if password == confpassword:
				#check which port is available and then increment by 10
				#if port is greater than 30000 then no user can be created
				port = mongo_port.db.ports.find_one({'username':'ports'})
				if port['port'] > 30000:
					return render_template('register.html',over=True)
				newport = port['port'] + 10
				#update port to newport
				result = mongo_port.db.ports.update_one({'username':'ports'},{'$inc': {'port':10}})
				url = str('http://songathon.xyz:'+str(newport)+'/'+username)
				newuser = mongo.db.users.insert_one({'username':username,'password':password,'email':email,'streaming':True,'port':newport,'url':url})
				return redirect(url_for('login'))
			else:
				#if the passwords dont mathch tell the user there passwords dont match
				return render_template('register.html',password=True)
	return render_template('register.html')


# #initdb
# @app.route('/api/initdb',methods=['POST','GET'])
# def initdb():
# 	mongo_port.db.ports.insert_one({'username':'ports','port':8000})
#login
@app.route('/api/login', methods=['POST','GET'])
def loginUser():
	data = json.loads(request.data)
	user = mongo.db.users.find_one({'username':data["username"]})
	try:
		if user["username"]:
			if str(user["username"]) == str(data["username"]):
				return jsonify({"user":user["username"], "port":str(user["port"]), "url":str(user["url"])})
	except Exception, e:
			return jsonify({"user":""})
	

#register
@app.route('/api/register', methods=['POST','GET'])
def registerUser():
	data = json.loads(request.data)
	user = mongo.db.users.find_one({'username':data["username"]})
	try:
		if user["username"]:
			return jsonify({"user":""})
	except Exception, e:
		#add user to db 
		port = mongo_port.db.ports.find_one({'username':'ports'})
		newport = port['port'] + 10
		result = mongo_port.db.ports.update_one({'username':'ports'},{'$inc': {'port':10}})
		url = str('http://songathon.xyz:'+str(newport)+'/'+str(data["username"]))
		newuser = mongo.db.users.insert_one({'username':str(data["username"]),'password':str(data["password"]),'email':str(data["email"]),'streaming':True,'port':newport,'url':url})
		return jsonify({"user":str(data["username"]), "port":str(newport), "url":str(url)})

#returns the list of users 
@app.route('/api/users', methods=['GET'])
def getUsers():
	streaming_users = mongo.db.users.find({'streaming':True})
	streaming_users = dumps(streaming_users)
	return jsonify({"users":streaming_users})

#this returns the songs searched by user
@app.route('/api/getsongs', methods=['POST','GET'])
def getSongs():
	data = json.loads(request.data)
	print data
	songs = cli.get_songs(data["search"])
	songs = dumps(songs)
	return jsonify({"songs":songs})


#takes song id, username and port then genrates stream
@app.route('/api/stream', methods=['POST'])
def streamSong():
	data = json.loads(request.data)
	#call(["kill","`fuser -n tcp "+str(data["port"])+" `"])
	call(["fuser","-k",str(data["port"]+"/tcp")])
	x = Genice(str(data["username"]),str(data["port"]))
	song = x.get_song(data["songid"]) 
	x.gen_files()
	x.gen_container()
	#update streaming attribute to True 
	#mongo.db.users.update_one({'username':str(current_user.id)},{'$set': {'streaming':True}})
	return jsonify({"good":"to go"})

def km2mile(x):
	'''a function to convert km to mile'''
	return int(x * 0.621371)

def calc_dist(lat1, lon1, lat2, lon2):
	'''a function to calculate the distance in miles between two 
	points on the earth, given their latitudes and longitudes in degrees'''
	# covert degrees to radians
	lat1 = math.radians(lat1)
	lon1 = math.radians(lon1)
	lat2 = math.radians(lat2)
	lon2 = math.radians(lon2)

	# get the differences
	delta_lat = lat2 - lat1
	delta_lon = lon2 - lon1

 	# print(delta_lat)
 	# print(delta_lon)

	# Haversine formula, 
	# from http://www.movable-type.co.uk/scripts/latlong.html
	a = ((math.sin(delta_lat/2))**2) + math.cos(lat1)*math.cos(lat2)*((math.sin(delta_lon/2))**2) 
	c = 2 * math.atan2(a**0.5, (1-a)**0.5)
	# earth's radius in km
	earth_radius = 6371 
	# return distance in miles
	return km2mile(earth_radius * c)


if __name__ == "__main__":
	socketio.run(app,debug=True,host='159.203.93.163',port=80)

