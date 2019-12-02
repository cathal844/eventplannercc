from flask import Flask, render_template, url_for, request, session, redirect, send_file, make_response, abort, Markup
import pymongo
import re
import sys
import bcrypt
from pymongo import MongoClient
import pymongo
app = Flask(__name__)
app.secret_key = 'mysecret'


mongo = pymongo.MongoClient('mongodb+srv://test:test1@cluster0-6m9qf.mongodb.net/test?retryWrites=true&w=majority', maxPoolSize=50, connect=False)

db = pymongo.database.Database(mongo, 'eventsplanner')
col = pymongo.collection.Collection(db, 'events')
col1 = pymongo.collection.Collection(db, 'eventsarchive')
users = pymongo.collection.Collection(db, 'users')


#route for landing page
@app.route("/")
def landing():

        return render_template('landing.html')


#route for home page once user is logged in
@app.route("/home")
def home():
        if 'email' in session:
                email = session['email']
        events = col.find({'email':email})
        print(email, file=sys.stderr)

        return render_template('home.html', events = events)

#route for removing event from table of events for the logged in user
@app.route("/home", methods=['POST', 'GET'])
def removeevent():
        if request.method == 'POST':
                if 'email' in session:
                        email = session['email']
                remove = request.form['remove']
                col.delete_one({'eventname': remove, 'email' : email})
                return redirect(url_for('home'))



#route to archive an event
@app.route("/archived-events", methods=['POST', 'GET'])
def addtoarhive():
        if request.method == 'POST':
                if 'email' in session:
                        email = session['email']
                add = request.form['add']
                name = col.find_one({'eventname': add, 'email' : email})['name']
                secondname = col.find_one({'eventname': add, 'email' : email})['email']
                eventname = col.find_one({'eventname': add, 'email' : email})['eventname']
                description = col.find_one({'eventname': add, 'email' : email})['description']
                location = col.find_one({'eventname': add, 'email' : email})['location']
                start_time = col.find_one({'eventname': add, 'email' : email})['start_time']
                end_time = col.find_one({'eventname': add, 'email' : email})['end_time']

                col1.insert({'name': name, 'email': email, 'eventname': eventname, 'description': description, 'location' : location, 'start_time' : start_time, 'end_time' : end_time})
                col.delete_one({'eventname': add, 'email' : email})
                return redirect(url_for('home'))

#route to search for an event
@app.route("/searchresults", methods=['POST', 'GET'])
def searchevents():
        if 'email' in session:
                        email = session['email']
        if request.method == 'POST':
                search = request.form['search']
                regx = re.compile(search, re.IGNORECASE)
                events = col.find({"eventname": regx, 'email': email})
        return render_template('search-results.html', events = events)

#route for the archived events table for the logged in user    
@app.route("/yourachivedevents")
def eventarchive():
        if 'email' in session:
                email = session['email']
        events = col1.find({'email':email})
        return render_template('archived-events.html', events = events)

#route to create an event for the logged in user 
@app.route("/createevent", methods=['POST', 'GET'])
def create():
    if request.method == 'POST':
        user = users.find_one({'email':session['email']})
        email = [user['email'], ""]
        name = user['name']
        event_name = request.form['event_name']
        description = request.form['description']
        location = request.form['location']
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        col.insert({'name': name, 'email': email, 'eventname': event_name, 'description': description, 'location' : location, 'start_time' : start_time, 'end_time' : end_time})
        return redirect(url_for('home'))

    return render_template('create-event.html')

#get name of the searched event
@app.route("/home", methods=['POST', 'GET'])
def getname():
        if request.method == 'POST':

                print(name, file=sys.stderr)
                return redirect(url_for('share', name = name))


#route to share an event to another user
@app.route("/shareresults", methods=['POST', 'GET'])
def shareevent():
        userss = users.find()
        if 'email' in session:
                email = session['email']
        events = col.find({'email':email})

        if request.method == 'POST':
                name = request.form['eventname']
                email1 = request.form['email1']
                col.update_one({'email':email, 'eventname': name}, {'$push': {'email': email1 }})

                return render_template('share-successful.html', email = email)



        return render_template('share-event.html', userss = userss, events = events)


# User Register
@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        existing_user = users.find_one({'email' : request.form['email']})

        if existing_user is None:
            hashpass = bcrypt.hashpw(request.form['pass'].encode('utf-8'), bcrypt.gensalt())
            name = request.form['name']
            email = request.form['email']
            users.insert({'name' : name, 'email' : email, 'password' : hashpass})
            session['email'] = request.form['email']
            return redirect(url_for('signin'))
        
        return 'That email already exists!'
    return render_template('register.html')



#login route
@app.route('/login', methods=['POST','GET'])
def login():
        incorrectDetails = "Invalid login, please try again"

        if request.method == 'POST':
                #login checking if the user is a teacher - due to email
                login = users.find_one({'email' : request.form['email']})
                incorrectDetails = "Invalid login, please try again"

                if login:

                        #Retriveing the entered password and encrypting it
                        #If statement checking if encrypted password is equal to password
                        if bcrypt.hashpw(request.form['password'].encode('utf-8'), login['password']) == login['password'] :
                                session['email'] = request.form['email']
                                return redirect(url_for('signin'))

        return render_template('login.html', incorrectDetails=incorrectDetails)

#route to get email of the signed in user
@app.route('/signin')
def signin():
    if 'email' in session:
        email = session['email']
        return redirect(url_for('home'))

    else:
        return render_template('landing.html')

@app.route('/test')
def test():

        return render_template('test.html')

#route to signout logged in user
@app.route('/')
def logout():
    session.pop('email', None)
    return render_template('login.html')


