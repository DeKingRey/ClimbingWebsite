"""Docstring Climbing Website
A climbing flask website to aid climbers to find climbs and communicate
By Miguel Monreal on 27/03/25"""

import sqlite3
import requests
import os 
import instructor
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()


from flask import Flask, render_template, redirect, url_for, send_from_directory, request, session

from flask_bcrypt import Bcrypt, check_password_hash
from flask_uploads import UploadSet, IMAGES, configure_uploads
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms.validators import DataRequired, Length, EqualTo, Optional, NoneOf, ValidationError
from wtforms import StringField, PasswordField, SubmitField

from slugify import slugify

from banned_words import BANNED_WORDS
#from profanity_filter import ProfanityFilter

from atomic_agents.agents.base_agent import  BaseAgent, BaseAgentConfig, BaseAgentInputSchema


app = Flask(__name__)
# This secret key is required for Flask-WTF to protect against CSRF attacks
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
# This sets the destination for uploaded photos to the 'uploads' folder 
app.config["UPLOADED_PHOTOS_DEST"] = "uploads"

bcrypt = Bcrypt(app)

# This is the variable which will hold the correct file type for images, getting the IMAGES variable which holds file types like png, jpg, gif, etc. It makes an upload set which is something which only allows certain file types(which is defined with the second parameter)
photos = UploadSet("photos", IMAGES)
# This configured the upload sets to the app, so will add previously defined 'photos' as one of the upload sets for this app
configure_uploads(app, photos)


def NoSpaces(message):
    def _no_spaces(form, field):
        if " " in field.data:
            raise ValidationError(message)
    return _no_spaces

# This creates a class which can be used to make forms(specifically for accounts)
class RegisterForm(FlaskForm):
    # Creates the name field which has to have input to be valid
    name = StringField("Name", validators=[DataRequired("Field should not be empty"),
                                           NoneOf(BANNED_WORDS, message="Please avoid using inappropriate language"),
                                           Length(min=3, max=20, message="Username must be between 3 and 20 characters long"),
                                           NoSpaces(message="Username must not contain spaces")
                                           ])
    # Creates a password field which can't be empty and has to be at least 8 characters long
    password = PasswordField("Password", validators=[
        DataRequired("Field should not be empty"), 
        Length(min=8, max=32, message="Password must be between 8 and 32 characters long"),
        NoSpaces(message="Password must not contain spaces")
        ])
    # Confirms that the user inputed the correct password by checking if it's the same as the previously defined Password
    confirm_password = PasswordField("Confirm_Password", validators=[EqualTo("password", "Passwords are not matching")])
    # Creates a file field where the profile picture can be uploaded
    photo = FileField(
        validators= [
            # Only allows the file types in the 'photos' upload set
            FileAllowed(photos, "Invalid file type"),
            # Is optional so the field can be empty and other errors will be ignored
            Optional()
        ]
    )

    # Creates the submit button which will check and validate the inputted data
    submit = SubmitField("Register")

# This is the url which is for the API
# Currently the API does not work so I will wait through the holidays to see if it continues to be like this
map_routes_url = "https://climbnz.org.nz/api/routes"


# These variables will be able to be accessed on every render template instead of manually inputting in every render
@app.context_processor
def inject_user():
    return {
        "username": session.get("username"),
        "profile_picture": session.get("profile_picture"),
        "permission_level": session.get("permission_level"),
        "display_name": session.get("display_name"),
        "date": session.get("date"),
    }


@app.route("/")
def home():
    user_id = session.get("user_id")
    
    if user_id is not None:
        # Gets accounts info when logging in
        con = sqlite3.connect("climbing.db")
        cur = con.cursor()
        cur.execute("SELECT profile_picture, username, permission_level, display_name, date FROM Account WHERE id = ?", (user_id,))
        result = cur.fetchone()
        profile_picture = result[0]
        username = result[1]
        permission_level = result[2]
        display_name = result[3]
        date = result[4]

        # Sets all session variables
        session["profile_picture"] = profile_picture
        session["username"] = username
        session["permission_level"] = permission_level
        session["display_name"] = display_name
        session["date"] = date
    else:
        profile_picture = None
        username = None
        permission_level = 0
        display_name = None
        date = None

    return render_template("home.html", header="Home")
    

# The climbing API I need to use is currently not working so I may need to come up with a workaround to this if it isn't fixed
@app.route("/map")
def map():
    # Calls the get map info function to get the marker coords
    markers = get_map_info()
    types = get_route_types()
    locations = get_locations()
    settings = get_settings()
    routes = get_routes()

    print(locations)

    return render_template("map.html", header="Map", markers=markers, types=types, locations=locations, settings=settings, climb_routes=routes)


def get_map_info():
    con = sqlite3.connect("climbing.db")
    cur = con.cursor()

    # Gets the info which will be used for the markers
    cur.execute("SELECT id, name, coordinates FROM Location WHERE pending = 0;")
    results = cur.fetchall()

    # Sets markers as an empty dictionary
    markers = {}
    for result in results: 
        # Makes a list with coords and name, with the coordinates split into a list(of latitude and longitude)
        info = [result[2].split(), result[1], slugify(result[1])]
        # Sets the ID as the key, and the previous list of info as the value
        markers[result[0]] = info
        
    return markers


def get_route_types():
    con = sqlite3.connect("climbing.db")
    cur = con.cursor()

    cur.execute("SELECT id, name FROM Type;")
    results = cur.fetchall()

    return results


def get_locations():
    con = sqlite3.connect("climbing.db")
    cur = con.cursor()

    cur.execute("SELECT name FROM Location WHERE pending = 0;")
    results = cur.fetchall()

    locations = []
    for location in results:
        locations.append(location[0]) 

    return locations


def get_routes():
    con = sqlite3.connect("climbing.db")
    cur = con.cursor()

    cur.execute("SELECT name FROM Route WHERE pending = 0;")
    results = cur.fetchall()

    routes = []
    for route in results:
        routes.append(route[0]) 

    return routes


def get_settings():
    con = sqlite3.connect("climbing.db")
    cur = con.cursor()

    cur.execute("SELECT id, name FROM setting;")
    results = cur.fetchall()

    return results


@app.route("/map/<string:name>")
def map_location(name):
    id = request.args.get("id")
    types = get_route_types()

    con = sqlite3.connect("climbing.db")
    cur = con.cursor()

    routes = get_routes()

    # Executes a query to join the Route_Type bridging table, and uses the current routes id
    cur.execute("""SELECT Location.name, Route.id, Route.name, Location.image FROM Location
                JOIN Route ON Route.location_id = Location.id
                WHERE Location.id = ? AND Route.pending = 0;""", (id,))
    
    results = cur.fetchall()
    if results == []: # If there are no routes only get location info
        cur.execute("SELECT name, id, image FROM Location WHERE id = ?;", (id,))
        info = cur.fetchall()
    else:
        location = results[0][0]
        image = results[0][3]
        # Makes a list with the location name, and then a dicitionary with the routes within it
        info = [[location, slugify(location), image], {}]

        for result in results:
            route_id = result[1]
            route_name = result[2]
            # Sets the key to the route id, and then the value is a list with the name and slugified name
            info[1][route_id] = [route_name, slugify(route_name)]

    return render_template("location.html", header="Map", info=info, types=types, climb_routes=routes)


@app.route("/map/<string:location>/<string:name>")
def map_route(location, name):
    con = sqlite3.connect("climbing.db")
    cur = con.cursor()

    # Gets the id from the query in the url
    id = request.args.get("id")

    # Executes a query to join the Route_Type bridging table, and uses the current routes id
    cur.execute("""SELECT Route.name, Type.name, grade, bolts, Location.name, Route.id
                FROM Route
                JOIN Route_Type ON Route.id = Route_Type.route_id
                JOIN Type ON Type.id = Route_Type.type_id
                JOIN Location on Route.location_id = Location.id
                WHERE Route.id = ?""", (id,))
    
    results = cur.fetchall()

    # Adds all the base info to the info list
    info = []
    for result in results[0]:
        info.append(result)
    
    # Sets an empty list inside info, and then takes all the types across all rows of results, to append those to the list within the list
    info[1] = []
    for type in results:
        info[1].append(type[1])

    return render_template("route.html", header="Map", info=info)


@app.route("/map/add-route", methods=["GET", "POST"])
def add_route():
    location_name = request.form.get("location")
    
    current_url = request.form.get("url")
    con = sqlite3.connect("climbing.db")
    cur = con.cursor()

    # Gets the location id
    cur.execute("SELECT id FROM Location WHERE name = ?", (location_name,))
    location_id = cur.fetchone()[0]

    # Sets all the field names
    fields = ["name", "grade", "bolts"]
    # Gets all the field values from the form, by looping through the fields list
    values = [request.form.get(field) for field in fields]

    types = request.form.getlist("types[]")

    # Will insert the values into the databse, first it uses the field names to define the columns, and then uses the length of fields to find the amount of '?'s, and uses values list as the values
    cur.execute(f"INSERT INTO Route ({', '.join(fields)}, location_id, pending) VALUES({', '.join('?' * len(fields))}, ?, 1)", values + [location_id])
    con.commit()

    # Gets the new routes id
    cur.execute("SELECT id FROM Route WHERE name = ?", (values[0],))
    route_id = cur.fetchone()[0]

    for type in types:
        cur.execute("INSERT INTO Route_Type (route_id, type_id) VALUES(?, ?)", (route_id, int(type)))

    con.commit()
    con.close()

    return redirect(current_url)


@app.route("/map/add-location", methods=["GET", "POST"])
def add_location():
    con = sqlite3.connect("climbing.db")
    cur = con.cursor()

    name = request.form.get("name")
    coordinates = f"{request.form.get('lat')} {request.form.get('lon')}"
    setting_id = request.form.get("setting")
    filename = photos.save(request.files["image"])
    file_url = url_for("get_file", filename=filename)

    cur.execute("INSERT INTO Location (name, coordinates, setting_id, image, pending) VALUES(?, ?, ?, ?, 1)", (name, coordinates, setting_id, file_url,))
    
    con.commit()
    con.close()

    return redirect(url_for("map"))


@app.route("/log-route", methods=["GET", "POST"])
def log_route():
    current_url = request.form.get("url")
    user_id = session.get("user_id")
    route_id = request.form.get("route_id")
    rating = request.form.get("rating")
    date = request.form.get("local_date")

    con = sqlite3.connect("climbing.db")
    cur = con.cursor()

    cur.execute("INSERT INTO Account_Route (account_id, route_id, rating, date) VALUES (?, ?, ?, ?)", (user_id, route_id, rating, date,))

    con.commit()
    con.close()

    return redirect(current_url)


@app.route("/posts", methods=["GET", "POST"])
def posts():
    return render_template("posts.html", header="Posts")


@app.route("/events", methods=["GET", "POST"])
def events():
    return render_template("events.html", header="Events")


@app.route("/admin")
def admin():
    con = sqlite3.connect("climbing.db")
    cur = con.cursor()

    cur.execute("""SELECT Route.id, Route.name, Location.name, GROUP_CONCAT(Type.name, ', '), Route.grade, Route.bolts FROM Route 
                JOIN Location ON Route.location_id = Location.id
                JOIN Route_Type ON Route.id = Route_Type.route_id
                JOIN Type ON Type.id = Route_Type.type_id
                WHERE Route.pending = 1
                GROUP BY Route.id;""")
    
    routes = cur.fetchall() # Gets all pending routes and their information

    cur.execute("""SELECT Location.id, Location.name, Location.coordinates, Setting.name, Location.image FROM Location
                JOIN Setting ON Location.setting_id = Setting.id
                WHERE Location.pending = 1;""")
    
    results = cur.fetchall() # Gets all pending locations and their information

    # Loops through results and properly formats the coordinates for google map links and then appends the new row to the locations array
    locations = []
    for result in results:
        coords = result[2].replace(" ", ",")
        row = [result[0], result[1], coords, result[3], result[4]]
        locations.append(row)

    con.close()

    return render_template("admin.html", header="Admin", routes=routes, locations=locations)


@app.route("/process-submission", methods=["GET", "POST"])
def process_submissions():
    con = sqlite3.connect('climbing.db')
    cur = con.cursor()

    id = request.form.get("id") 
    type = request.form.get("type") # Used to identify which table to alter
    action = request.form.get("action") # Either approve or deny

    if action == "approve":
        cur.execute(f"UPDATE {type} SET pending = 0 WHERE id = ?;", (id,))  # Sets pending to false, approving the submission
    else:
        cur.execute(f"DELETE FROM {type} WHERE id = ?;", (id,)) # Removes the submission
        if type == "Route":
            cur.execute(f"DELETE FROM Route_Type WHERE route_id = ?;", (id,)) # Deletes the routes types if it is a route

    con.commit()
    con.close()
    
    return redirect(url_for('admin'))


@app.route("/account", methods=["GET", "POST"])
def account():
    routes = None
    if session.get("user_id"): # Makes sure the user is logged in
        routes = get_logged_routes()

    if request.method == "POST":
        action = request.form.get("action") # Gets the action of the form

        if action == "edit":
            return redirect(url_for("edit_account")) # R    edirects to edit if edit button is pressed

        if action == "logout":
            logout()
            return redirect(url_for("home")) # Logs out and goes to home if logout is pressed
    return render_template("account.html", header="Account", routes=routes)


def get_logged_routes():
    con = sqlite3.connect("climbing.db")
    cur = con.cursor()

    # Gets the logged routes info for the current account
    cur.execute("""SELECT Route.name, Account_Route.rating, Account_Route.date
                FROM Account_Route
                JOIN Route ON Account_Route.route_id = Route.id
                WHERE Account_Route.account_id = ?;
                """, (session.get("user_id"),))

    return cur.fetchall()


@app.route("/edit_account", methods=["GET", "POST"])
def edit_account():
    errors = {"username": [],
                "display_name": [],
                "profile_picture": []
                } # Dictionary of errors
    if request.method == "POST":
        action = request.form.get("action")

        if action == "apply":
            username = request.form.get("username").strip()
            display_name = request.form.get("display_name").strip()

            if profanity_check(username):
                errors["username"].append("Username contains inappropriate language.") # Makes sure the username and display name aren't innappropriate
            if not username:
                errors["username"].append("Username cannot be empty.")

            # Makes sure the username isn't too short or too long
            if len(username) > 20: 
                errors["username"].append("Username must be under 20 characters long")
            if len(username) < 3:
                errors["username"].append("Username must be over 3 characters long")

            if profanity_check(display_name):
                errors["display_name"].append("Display name contains inappropriate language.")
            if not display_name:
                display_name = username

            # Makes sure the display name isn't too short or too long
            if len(display_name) > 20: 
                errors["display_name"].append("Display name must be under 20 characters long")
            if len(display_name) < 3:
                errors["display_name"].append("Display name must be over 3 characters long")

            if not any(errors.values()): # Only runs if there are no errors 
                try:
                    profile_picture = request.files.get("image") # Gets all the inputs and strips them

                    if profile_picture and profile_picture.filename != "": # Makes sure the profile picture was updated
                        filename = photos.save(profile_picture) # Saves the pfp to uploads
                        file_url = url_for("get_file", filename=filename) # Gets the url for it 
                    else:
                        file_url = request.form.get("current_profile") # If the pfp wasn't updated it stays as the current

                    con = sqlite3.connect("climbing.db")
                    cur = con.cursor()

                    cur.execute("UPDATE Account SET username = ?, display_name = ?, profile_picture = ? WHERE username = ?", 
                                (username, display_name, file_url, session.get("username"))) # Updates the account with the new info
                    con.commit()
                    con.close()

                    session["profile_picture"] = file_url
                    session["username"] = username
                    session["display_name"] = display_name # Sets the new inputs

                    return redirect(url_for("account"))
                except sqlite3.IntegrityError:
                    errors["username"].append("This username is already taken") # If there is an error, the username is not unique
        else: 
            return redirect(url_for("account"))

    return render_template("edit_account.html", header="Account", errors=errors)


def profanity_check(text):
    return any(banned_word in text.lower() for banned_word in BANNED_WORDS) # Returns true if the text contains a banned word


@app.route("/register", methods=["GET", "POST"])
def register():
    con = sqlite3.connect("climbing.db")
    cur = con.cursor()
    
    wtf_form = RegisterForm()

    if wtf_form.validate_on_submit():
        name = wtf_form.name.data
        password = wtf_form.password.data
        date = request.form.get("local_date")
        
        # This hashes the password making it secure and able to be stored in a database. Hashed things cannot be unhashed so it is quite secure
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        
        try:
            # This saves the photos file in the uploads folder
            if wtf_form.photo.data != None:
                # This saves the file in the uploads folder and gets the filename
                filename = photos.save(wtf_form.photo.data)
            else:
                # Guest Profile Picture
                # If there is no photo input then the users profile picture will be set to the guest profile picture
                filename = "magnus.png"
            # This will get the files url from the get_file() function
            file_url = url_for("get_file", filename=filename)

            # This executes an SQL stament which adds the users registry information to the database
            cur.execute("INSERT INTO Account (username, password, profile_picture, permission_level, display_name, date) VALUES (?, ?, ?, 1, ?, ?)", (name, hashed_password, file_url, name, date))
            con.commit()

            session["user_id"] = cur.lastrowid # Auto logs in by getting the id of the last inserted row
            return redirect(url_for("home"))
        except sqlite3.IntegrityError:
            wtf_form.name.errors.append("That username is already taken")

    return render_template("register.html", form=wtf_form, header="Register")


@app.route("/uploads/<filename>")
def get_file(filename):
    # This will create a link for the file from the uploads folder directory using the filename
    return send_from_directory(app.config["UPLOADED_PHOTOS_DEST"], filename)


@app.route("/login", methods=["GET", "POST"])
def login():
    # Sets error to None in case there are no errors
    error = None

    # Checks if their is a post request
    if request.method == "POST":
        # Sets the username and password to the inputted data
        username = request.form.get("username")
        password = request.form.get("password") 

        # Connects to the database
        con = sqlite3.connect("climbing.db")
        cur = con.cursor()
        # Checks if user is in database
        cur.execute("SELECT id, password FROM Account WHERE username = ?;", (username,))
        result = cur.fetchone()
    
        if result:
            correct_password = result[1]
            # Checks if the inputted password matches the stored hashed password
            if check_password_hash(correct_password, password):
                # Saves the user's id to the session so it can be used anywhere, though is cleared when they leave the website 
                session["user_id"] = result[0]
                # Redirects the user to home
                return redirect(url_for("home"))
            else:
                error = "Password is incorrect."
        else:
            error = "Username not found."

    return render_template("login.html", header="Login", error=error)


def logout():
    session["user_id"] = None
    session["profile_picture"] = None
    session["username"] = None
    session["permission_level"] = None
    session["display_name"] = None
    session["date"] = None


if __name__ == "__main__":
    app.run(debug=True)
