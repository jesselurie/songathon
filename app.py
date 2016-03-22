
import json
import requests
import soundcloud_cli
from flask import Flask,jsonify,url_for,render_template,request,redirect
from flask.ext.pymongo import PyMongo
from genice import *
from docker import Client
from subprocess import call

cli_doc = Client(base_url='unix://var/run/docker.sock')
cli = soundcloud_cli.Soundc()

app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!
app.config['config_prefix']='MONGO'
app.config['MONGO_HOST'] ='songathon.xyz'
app.config['MONGO_DBNAME'] = 'users'
app.config['MONGO_PORT'] = 27017
mongo = PyMongo(app,config_prefix='MONGO')

app.config['config_prefix']='MONGO2'
app.config['MONGO2_HOST'] ='songathon.xyz'
app.config['MONGO2_DBNAME'] = 'ports'
app.config['MONGO2_PORT'] = 27017
mongo_port = PyMongo(app,config_prefix='MONGO2')

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
	#blah = mongo_port.db.ports.insert_one({'username':'ports','port':8000})
	#query db and find all users that streming attribute is True
	#mongo.db.users.update_one({'username':str(current_user.id)},{'$set': {'streaming':False}})
	streaming_users = mongo.db.users.find({'streaming':True})
	return render_template('stream.html',streaming_users=streaming_users)

@app.route('/turnup',methods=['POST','GET'])
def turnup():
	#template this so the url is the username
	return render_template('streaming.html',url=request.form['url'],username=request.form['username'])
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


if __name__ == "__main__":
	app.run(debug=True,host='159.203.93.163',port=80)

