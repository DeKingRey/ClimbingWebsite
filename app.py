"""Docstring Climbing Website
A climbing flask website to aid climbers to find climbs and communicate
By Miguel Monreal on 27/03/25"""

import sqlite3
import os 
from dotenv import load_dotenv
from datetime import datetime 
load_dotenv()


from flask import Flask, render_template, redirect, url_for, send_from_directory, request, session, jsonify, flash

from flask_bcrypt import Bcrypt, check_password_hash
from flask_uploads import UploadSet, IMAGES, configure_uploads, UploadNotAllowed
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms.validators import DataRequired, Length, EqualTo, Optional, NoneOf, ValidationError
from wtforms import StringField, PasswordField, SubmitField

from slugify import slugify

from banned_words import BANNED_WORDS


app = Flask(__name__)
# This secret key is required for Flask-WTF to protect against CSRF attacks
# app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SECRET_KEY"] = "T8OR437B9&i#e^*&b)p(*:o#iuef(*yoliu))"
# Sets the destination for uploaded photos to the 'uploads' folder and configures uploads
app.config["UPLOADED_PHOTOS_DEST"] = "uploads"
photos = UploadSet("photos", IMAGES)
configure_uploads(app, photos)

bcrypt = Bcrypt(app)


def NoSpaces(message):
    def _no_spaces(form, field):
        # Raises error if there is a space in the error
        if " " in field.data:
            raise ValidationError(message)
    return _no_spaces


# This creates a class which can be used to make forms(specifically for accounts)
class RegisterForm(FlaskForm):
    # Username field with validation for length and profanitys
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
    # Validatation of confirm password field matching password
    confirm_password = PasswordField("Confirm_Password", validators=[EqualTo("password", "Passwords are not matching")])
    # Creates a file field where the profile picture can be optionally uploaded
    photo = FileField(
        validators= [
            # Only allows the file types in the 'photos' upload set
            FileAllowed(photos, "Invalid file type"),
            Optional()
        ]
    )

    # Submit validation button
    submit = SubmitField("Register")


# Inject user session info into all templates
@app.context_processor
def inject_user():
    return {
        "user_id": session.get("user_id"),
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
        # Gets accounts info when logging in to be used across the website
        con = sqlite3.connect("climbing.db")
        cur = con.cursor()
        cur.execute("SELECT profile_picture, username, permission_level, display_name, date FROM Account WHERE id = ?", (user_id,))
        result = cur.fetchone()
        # Sets all session variables
        session["profile_picture"] = result[0]
        session["username"] = result[1]
        session["permission_level"] = result[2]
        session["display_name"] = result[3]
        session["date"] = result[4]
        con.close()
    else:
        profile_picture = None
        username = None
        permission_level = 0
        display_name = None
        date = None

    return render_template("home.html", header="Home")
    

@app.route("/map")
def climbing_map():
    # Calls the get map info function to get the marker coords
    markers = get_map_info()
    types = get_route_types()
    locations = get_locations()
    settings = get_settings()
    routes = get_routes()

    return render_template("map.html", header="Map", markers=markers, types=types, locations=locations, settings=settings, climb_routes=routes)


def get_map_info():
    con = sqlite3.connect("climbing.db")
    cur = con.cursor()

    # Gets the info which will be used for the markers
    cur.execute("SELECT id, name, coordinates FROM Location WHERE pending = 0;")
    results = cur.fetchall()

    markers = {}
    for result in results: 
        # Makes a list with coords and name and splits them to be used individually
        info = [result[2].split(), result[1], slugify(result[1])]
        # Sets the ID as the key, and the previous list of info as the value to use for all markers
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

    cur.execute("SELECT id FROM Location WHERE name = ?", (location_name,))
    location_id = cur.fetchone()[0]

    # Sets all the field names for inserting
    fields = ["name", "grade", "bolts"]
    # Gets all the field values from the form, by looping through the fields list
    values = [request.form.get(field) for field in fields]

    types = request.form.getlist("types[]")

    # Will insert the values into the database using the given field names and values
    cur.execute(f"INSERT INTO Route ({', '.join(fields)}, location_id, pending) VALUES({', '.join('?' * len(fields))}, ?, 1)", values + [location_id])
    con.commit()

    # Gets the new routes id
    cur.execute("SELECT id FROM Route WHERE name = ?", (values[0],))
    route_id = cur.fetchone()[0]

    for type in types:
        cur.execute("INSERT INTO Route_Type (route_id, type_id) VALUES(?, ?)", (route_id, int(type)))

    con.commit()
    con.close()
    flash("Your route is now pending approval", "info")

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
    flash("Your location is now pending approval", "info")

    return redirect(url_for("climbing_map"))


@app.route("/log-route", methods=["GET", "POST"])
def log_route():
    current_url = request.form.get("url")
    user_id = session.get("user_id")
    route_id = request.form.get("route_id")
    rating = request.form.get("rating")
    date = request.form.get("local_date")
    errors = {}
    
    con = sqlite3.connect("climbing.db")
    cur = con.cursor()

    # Gets all routes ids 
    cur.execute("SELECT id FROM Route")
    results = cur.fetchall()
    route_ids = [str(id[0]) for id in results]

    # Validates that the route id exists
    if route_id not in route_ids:
        errors.setdefault("other", []).append("Route id does not exist")

    # Validates that the rating is between 1-5 and is an int
    try:
        if int(rating) < 1 or int(rating) > 5:
            errors["rating"] = "Rating must be between 1 and 5"
    except ValueError:
        errors["rating"] = "Rating must be a number"
    
    # Validates log date
    if date:
        try:
            post_date = datetime.strptime(date, "%d-%m-%Y")
            today = datetime.today()

            # Makes sure it is the current date
            if post_date.date() != today.date():
                errors.setdefault("other", []).append("Log date must be today")
        except ValueError:
            "Invalid post date format"
    else:
        errors.setdefault("other", []).append("Log date required")

    if not errors:
        cur.execute("SELECT 1 FROM Account_Route WHERE account_id = ? AND route_id = ?;", (user_id, route_id,))
        existing_entry = cur.fetchone()

        # Checks if the user has already logged, if so update info, if not insert it
        if existing_entry:
            cur.execute("UPDATE Account_Route SET rating = ?, date = ? WHERE account_id = ? AND route_id = ?;", 
                        (rating, date, user_id, route_id,))
        else:
            cur.execute("INSERT INTO Account_Route (account_id, route_id, rating, date) VALUES (?, ?, ?, ?)", (user_id, route_id, rating, date,))

        con.commit()
        con.close()
        flash("Route logged!", "success")
    else:
        flash(errors, "log_errors")
        flash("Invalid Form Submission", "error")

    return redirect(current_url)


@app.route("/events", methods=["GET", "POST"])
def events():
    events = get_events(0)

    return render_template("events.html", header="Events", events=events)


@app.route("/events/<string:event_slug>", methods=["GET", "POST"])
def event(event_slug):
    con = sqlite3.connect("climbing.db")
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    event_id = request.args.get("id")

    errors = {}
    submitted_results = []

    # Will validate and publish results to database
    if request.method == "POST":
        errors = {}
        submitted_results = []
        # Gets the ID's that have joined the event to validate later
        valid_info = get_results(event_id)
        valid_ids = [str(p["id"]) for p in valid_info]
        num_participants = len(valid_info)

        # If time is inputted once it must be inputted everywhere else
        time_required = False

        i = 1
        # Loops through all published result entries validating inputs then adding them
        for i in range(1, num_participants + 1):
            account_id = request.form.get(f"account_id_{i}")
            time_mins = request.form.get(f"time_mins_{i}")
            time_secs = request.form.get(f"time_secs_{i}")

            time = None

            # Validates time inputs
            if time_mins or time_secs:
                time_required = True
                if not time_mins or not time_secs:
                    errors.setdefault(f"time_{i}", []).append("Both minutes and seconds are required")
                # Ensures time inputs are a number
                elif not time_mins.isnumeric() or not time_secs.isnumeric():
                    errors.setdefault(f"time_{i}", []).append("Time must be numeric and non negative") 
                else:
                    # Ensures time inputs aren't too long or negative
                    mins = int(time_mins)
                    secs = int(time_secs)
                    if not (0 <= mins <= 100) or not (0 <= secs <= 59):
                        errors.setdefault(f"time_{i}", []).append("Time must be a valid input")
                    else:
                        # Forms the time string if both inputs are gotten
                        time = f"{time_mins}:{secs:02d}mins"

            # Only validates results for a valid participant
            if  account_id:    
                # Prevents altering account_id value to an ID not in the event
                if account_id not in valid_ids:
                    errors[f"account_id_{i}"] = "Invalid participant ID"

                # If time is inputted anywhere but not provided in one spot
                if time_required and not time: 
                    errors.setdefault(f"time_{i}", []).append("Time must be filled in if provided anywhere")
                
                # Appends a dict of the results
                submitted_results.append({
                    "account_id": int(account_id),
                    "placing": i,
                    "time": time if time_required else None
                })
            elif time_mins or time_secs:
                errors[f"account_id_{i}"] = "Missing participant ID for entry"

        # Will let the html know if there are any time errors
        if any(key.startswith("time_") for key in errors):
            errors["has_time_errors"] = True

        # If there are no errors then the data will be inserted       
        if not errors:
            con = sqlite3.connect("climbing.db")
            cur = con.cursor()
            
            # Inserts each result iteratively
            for result in submitted_results:
                if time_required:
                    cur.execute("UPDATE Account_Event SET placing = ?, TIME = ? WHERE account_id = ? AND event_id = ?;", 
                                (result["placing"], result["time"], result["account_id"], event_id))
                else: # If time is not inputted 
                    cur.execute("UPDATE Account_Event SET placing = ?WHERE account_id = ? AND event_id = ?;",
                                (result["placing"], result["account_id"], event_id))
            con.commit()
            con.close()
            flash("Results added!", "success")
            return redirect(url_for("event", event_slug=event_slug, id=event_id))

    # Gets all the events info
    cur.execute("""SELECT Event.id, Event.name, post_date, start_date, end_date, Event.description, Event.full_description,
                location, Account.display_name AS name, start_time, end_time, Event.pending, Event.image, 
                Account.id AS host_id
                FROM Event
                JOIN Account ON Event.account_id = Account.id
                WHERE Event.pending = 0 AND Event.id == ?;""", (event_id,))
    event_data = cur.fetchone()
    
    # Will be used to find whether the user has joined the event
    cur.execute("SELECT event_id FROM Account_Event WHERE account_id = ? AND event_id = ?;", (session.get("user_id"), event_id,))
    joined = cur.fetchone()

    event_dict = dict(event_data) # Turns event into a dict

    # Sets the joined bool to determine whether the event is joined by the user or not
    event_dict["joined"] = joined is not None

    event_dict["slug"] = event_slug

    status = event_status(event_dict) # Gets the status of the event
    results = dict()
    participants = dict()
    no_results = False

    # If the event is concluded get the result info
    if status == 4:
        results_data = get_results(event_id)

        # Prevent error from participantless event
        if results_data:
            # Checks whether the results are published or not
            if results_data[0].get("placing"):
                results = results_data
            else:
                participants = results_data # Will be used in the publish results form
        else:
            no_results = True
    
    con.close()

    return render_template(
        "event.html", 
        event=event_dict, 
        results=results, 
        participants=participants, 
        no_results=no_results, 
        errors=errors,
        submitted_results=submitted_results
    )


@app.route("/event-action", methods=["POST"])
def event_action():
    # This will handle the functionality of the buttons on each event

    action = request.form.get("action") # Gets the buttons action
    account_id = session.get("user_id")
    event_id = request.form.get("event_id")

    if not account_id:
        return jsonify({"status": "login"}) # Passes the json to login if account id isn't found
    
    con = sqlite3.connect("climbing.db")
    cur = con.cursor()

    if action == "join":
        try:
            # Inserts the values into the account_event bridging table
            cur.execute("INSERT INTO Account_Event (account_id, event_id) VALUES (?, ?)", (account_id, event_id,))
            con.commit()
            status = "joined"
        except sqlite3.IntegrityError: # In case the user has already joined the event
            pass
    elif action == "leave":
        # Deletes the user from the event they joined
        cur.execute("DELETE FROM Account_Event WHERE account_id = ? AND event_id = ?;", (account_id, event_id,))
        con.commit()
        status = "left"
    else:
        status = "error" # Error if anything else

    con.close()
    return jsonify({"status": status}) # Returns the status for JS


def get_events(pending):
    con = sqlite3.connect("climbing.db")
    con.row_factory = sqlite3.Row # Returns results as a dictionary to be accessed easier for me

    cur = con.cursor()
    # Gets all events info
    cur.execute("""SELECT Event.id, Event.name, post_date, start_date, end_date, Event.description, 
                location, Account.display_name, start_time, end_time, Event.pending, Event.image
                FROM Event
                JOIN Account ON Event.account_id = Account.id
                WHERE Event.pending = ?;""", (pending,))
    events = cur.fetchall()

    # Converts the events sql dict into a python array of dicts so I can add values
    events = [dict(event) for event in events]

    # The joined events will be organised and ordered if the event isn't pending
    if pending == 0:
        # Sets joined events to none as it will only be needed if the user is logged in
        joined_events_ids = set()
        if session.get("user_id"):
            user_id = session.get("user_id")      

            # Gets every event the user has joined and adds their ids to a set
            cur.execute("SELECT event_id FROM Account_Event WHERE account_id = ?;", (user_id,))
            joined_events_ids = {row["event_id"] for row in cur.fetchall()}

        # Adds joined events keys to the events dict 
        for event in events:
            event["joined"] = event["id"] in joined_events_ids
            event["slug"] = slugify(event["name"]) # Creates a slug for the event so the name can be properly used in a link
        
        # Sorts by status: Ongoing joined > Ongoing > Upcoming joined > Upcoming > Concluded, then by nearest time(start or end)
        events.sort(key=sort_events)

    con.close()
    return events


@app.route("/events/add-event", methods=["GET", "POST"])
def add_event():
    locations = get_locations()
    errors = {}

    # Will validate and insert the event
    if request.method == "POST":
        # Gets the fields and values from the form and turns them into a dict
        fields = ["name", "start_date", "end_date", "start_time", "end_time", "location", "description", "full_description", "post_date", "account_id"]
        values = {field: request.form.get(field) for field in fields}

        # Validates name input
        if values["name"]:
            if len(values["name"]) < 3 or len(values["name"]) > 100:
                errors["name"] = "Event title must be between 3 and 100 characters"
        else:
            errors["name"] = "Event title required"
        
        # Validates date and time inputs
        if all(values.get(key) for key in ["start_date", "end_date", "start_time", "end_time"]):
            try:
                # Gets values which will be used to validate the inputted datetime
                start_value = datetime.strptime(f"{values['start_date']} {values['start_time']}", "%Y-%m-%d %H:%M")
                end_value = datetime.strptime(f"{values['end_date']} {values['end_time']}", "%Y-%m-%d %H:%M")
                now = datetime.now()

                # Makes sure datetimes are in the future and correctly ordered 
                if start_value < now or end_value < now:
                    errors["datetime"] = "Date and time must be in the future"
                elif start_value > end_value:
                    errors["datetime"] = "Start datetime must be before end datetime"

                # Converts date and times into a readable format
                values["start_date"] = start_value.strftime("%d-%m-%Y") 
                values["end_date"] = end_value.strftime("%d-%m-%Y")
                values["start_time"] = start_value.strftime("%I:%M%p").lower()
                values["end_time"] = end_value.strftime("%I:%M%p").lower()
            except ValueError:
                # Ensures they are the write input type
                errors["datetime"] = "Invalid date or time format"
        else:
            errors["datetime"] = "Dates and times are required"

        # Validates location name input
        if values["location"]:
            if len(values["location"]) < 3 or len(values["location"]) > 100:
                errors["location"] = "Location name must be between 3 and 100 characters"
        else:
            errors["location"] = "Location name required"

        # Validates brief description input
        if values["description"]:
            if len(values["description"]) < 50 or len(values["description"]) > 250:
                errors["description"] = "Brief description must be between 50 and 250 characters"
        else:
            errors["description"] = "Brief description required"

        # Validates full description input
        if values["full_description"]:
            if len(values["full_description"]) < 100 or len(values["full_description"]) > 1000:
                errors["full_description"] = "Full description must be between 100 and 1000 characters"
        else:
            errors["full_description"] = "Full description required"
        
        # Validates post date
        if values["post_date"]:
            try:
                post_date = datetime.strptime(values["post_date"], "%d-%m-%Y")
                today = datetime.today()

                # Makes sure it is the current date
                if post_date.date() != today.date():
                    errors.setdefault("other", []).append("Post date must be today")
            except ValueError:
                "Invalid post date format"
        else:
            errors.setdefault("other", []).append("Post date required")

        # Validates that account id is the current users id
        if values["account_id"] != str(session.get("user_id")):
            errors.setdefault("other", []).append("Account ID is invalid")

        # Validates image input
        image_file = request.files.get("image")
        if not image_file or image_file.filename.strip() == "":
            errors["image"] = "Image required"
        else:
            try:
                # Attempts to save the filename
                saved_filename = photos.save(image_file)

                file_url = url_for("get_file", filename=saved_filename)
            except UploadNotAllowed:
                errors["image"] = "Invalid image file type"
        
        if errors == {}:
            con = sqlite3.connect("climbing.db")
            cur = con.cursor()
            cur.execute(f"""INSERT INTO Event ({' ,'.join(field for field in values)}, image, pending) 
                        VALUES({', '.join('?' * len(fields))}, ?, 1)""",
                        tuple(values[value] for value in values) + (file_url,))

            con.commit()
            con.close()

            flash("Your event is now pending approval", "info")
            return redirect(url_for("events"))
    return render_template("add-event.html", header="Events", locations=locations, errors=errors)


def get_results(id):
    con = sqlite3.connect("climbing.db")
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    cur.execute("""SELECT ae.placing, a.display_name AS name, a.username, ae.time, a.id
            FROM Account_Event ae
            JOIN Account a ON ae.account_id = a.id
            WHERE ae.event_id = ?;""", (id,))
    data = cur.fetchall()
    data_dict = [dict(info) for info in data]
    
    results = dict()
    # If the results are available order and suffix the placings for table visibility
    if data_dict:
        if data_dict[0].get("placing"):
            results = sorted(data_dict, key=lambda item: item["placing"])

            for result in results:
                result["placing"] = placing_suffix(result["placing"])
            return results
    return data_dict # Either list of participants, or None(if no participants)


def parse_datetime(date, time):
    day, month, year = map(int, date.split("-")) # Separates day time and month
    hour, minute = map(int, time[:-2].split(":")) # Separates hours and minutes, ignoring the meridian for now
    ampm = time[-2:]    

    # Following if statements convert the hours into 24hr time 
    if ampm == "pm" and hour != 12: # Add 12 hours if its pm and not 12pm
        hour += 12
    if ampm == "am" and hour == 12: # If it's midnight
        hour = 0
    
    return datetime(year, month, day, hour, minute) # Converts into a python datetime


def event_status(event):
    now = datetime.now() # Gets current time
    start = parse_datetime(event["start_date"], event["start_time"])
    end = parse_datetime(event["end_date"], event["end_time"])

    # Gets the events status
    if start <= now <= end: # If the event has started but not ended
        if (event["joined"]):
            return 0 # Ongoing joined
        else:
            return 1 # Ongoing not joined
    elif now < start:
        if (event["joined"]):
            return 2 # Upcoming joined
        else:
            return 3 # Upcoming not joined
    else:
        return 4 # Concluded


def sort_events(event):
    # Will sort events status by how soon they are starting/ending
    status = event_status(event)
    if status <= 1 or status == 4: # Ongoing or concluded events are sorted by when they will/have ended
        sort_time = parse_datetime(event["end_date"], event["end_time"])
    else: # Upcoming events are sorted by when they start
        sort_time = parse_datetime(event["start_date"], event["start_time"])

    print(f"Event: {event['name']} | Status: {status} | Sort Time: {sort_time}")
    return(status, sort_time.timestamp())


def placing_suffix(placing):
    if 11 <= placing <= 13: # 11-13 are different to other numbers as they have a th suffix instead of other 1's, 2's, and 3's
        suffix = "th"
    elif placing % 10 == 1: # Checks if the remainder of the plaing % 10 is 1, e.g. 10 fits into 21 twice, 21-20 = 1
        suffix = "st"
    elif placing % 10 == 2:
        suffix = "nd"
    elif placing % 10 == 3:
        suffix = "rd"
    else:
        suffix = "th"
    return str(f"{placing}{suffix}") # Updates the event placing


@app.route("/admin")
def admin():
    con = sqlite3.connect("climbing.db")
    cur = con.cursor()

    cur.execute("""SELECT Route.id, Route.name, Location.name, GROUP_CONCAT(Type.name, ', '), Route.grade, Route.bolts FROM Route 
                LEFT JOIN Location ON Route.location_id = Location.id
                LEFT JOIN Route_Type ON Route.id = Route_Type.route_id
                LEFT JOIN Type ON Type.id = Route_Type.type_id
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

    # Gets all pending events
    events = get_events(1)

    con.close()

    return render_template("admin.html", header="Admin", routes=routes, locations=locations, events=events)


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
    events = None
    submissions = {}
    if session.get("user_id"): # Makes sure the user is logged in
        routes = get_logged_routes()
        events = get_joined_events()

        con = sqlite3.connect("climbing.db")
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        user_id = session.get("user_id")
        # Gets all routes/locations/events that are pending and made by the user, also adds a type column 
        cur.execute("""
                SELECT 'Route' AS type, name, NULL, NULL
                FROM Route
                WHERE account_id = ? AND pending = 1
                UNION ALL
                SELECT 'Location' AS type, name, NULL, NULL
                FROM Location
                WHERE account_id = ? AND pending = 1
                UNION ALL
                SELECT 'Event' AS type, name, NULL, NULL
                FROM Event
                WHERE account_id = ? AND pending = 1
            """, (user_id, user_id, user_id))
        results = cur.fetchall()
        
        submissions_results = [dict(row) for row in results]
        types = ["Route", "Location", "Event"]
        i = 0
        for result in submissions_results:
            submissions.setdefault(types[i], []).append(result)
            if result["type"] != types[i]:
                i += 1

    if request.method == "POST":
        action = request.form.get("action") # Gets the action of the form

        if action == "edit":
            return redirect(url_for("edit_account")) # R    edirects to edit if edit button is pressed

        if action == "logout":
            logout()
            return redirect(url_for("home")) # Logs out and goes to home if logout is pressed
    return render_template("account.html", header="Account", routes=routes, events=events, submissions=submissions)


def get_logged_routes():
    con = sqlite3.connect("climbing.db")
    cur = con.cursor()

    # Gets the logged routes info for the current account
    cur.execute("""SELECT Route.name, Account_Route.rating, Account_Route.date
                FROM Account_Route
                JOIN Route ON Account_Route.route_id = Route.id
                WHERE Account_Route.account_id = ?;
                """, (session.get("user_id"),))
    results = cur.fetchall()
    con.close()

    return results


def get_joined_events():
    con = sqlite3.connect("climbing.db")
    con.row_factory = sqlite3.Row # Turns the results into a table for easier access of values
    cur = con.cursor()
    
    # Gets relevant event info and user results 
    cur.execute("""SELECT e.id, e.name, start_date, end_date, start_time, end_time, ae.placing, ae.time
                FROM Account_Event ae
                JOIN Event e ON ae.event_id = e.id
                WHERE ae.account_id = ?
                """, (session.get("user_id"),))
    results = cur.fetchall()
    con.close()

    events = [dict(result) for result in results]
    for event in events:
        event["slug"] = slugify(event["name"])
        event["joined"] = True
        event["concluded"] = event_status(event) == 4 # Will be true or false depending on what event status returns

        # Adds the placing suffix e.g. 1st, 2nd, 3rd, 4th
        if event["placing"]:
            event["placing"] = placing_suffix(event["placing"])

    events.sort(key=event_status) # Sorts based on the status returned
    return events


@app.route("/edit_account", methods=["GET", "POST"])
def edit_account():
    errors = {"username": [],
                "display_name": [],
                "profile_picture": []
                }
    if request.method == "POST":
        action = request.form.get("action")

        # Validates then applies edits made
        if action == "apply":
            username = request.form.get("username").strip()
            display_name = request.form.get("display_name").strip()

            # Checks if user and display name are correct length, not profanic, and are inputted
            if profanity_check(username):
                errors["username"].append("Username contains inappropriate language.")
            if not username:
                errors["username"].append("Username cannot be empty.")

            if len(username) > 20: 
                errors["username"].append("Username must be under 20 characters long")
            if len(username) < 3:
                errors["username"].append("Username must be over 3 characters long")

            if profanity_check(display_name):
                errors["display_name"].append("Display name contains inappropriate language.")
            if not display_name:
                display_name = username

            if len(display_name) > 20: 
                errors["display_name"].append("Display name must be under 20 characters long")
            if len(display_name) < 3:
                errors["display_name"].append("Display name must be over 3 characters long")

            # If names are error free
            if not any(errors.values()):
                try:
                    profile_picture = request.files.get("image")

                    # Checks if the profile picture was updated and saves it
                    if profile_picture and profile_picture.filename != "":
                        filename = photos.save(profile_picture)
                        file_url = url_for("get_file", filename=filename) 
                    else:
                        file_url = request.form.get("current_profile") # Set pfp to the current if unchanged

                    con = sqlite3.connect("climbing.db")
                    cur = con.cursor()

                    # Updates account info
                    cur.execute("UPDATE Account SET username = ?, display_name = ?, profile_picture = ? WHERE username = ?", 
                                (username, display_name, file_url, session.get("username")))
                    con.commit()
                    con.close()

                    session["profile_picture"] = file_url
                    session["username"] = username
                    session["display_name"] = display_name 

                    return redirect(url_for("account"))
                except sqlite3.IntegrityError: # Ensures username is unique
                    errors["username"].append("This username is already taken")
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
        
        # Secures password by hashing it to avoid issues
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        
        try:
            # Save profile if provided
            if wtf_form.photo.data != None:
                filename = photos.save(wtf_form.photo.data)
            else: 
                # Guest Profile Picture
                filename = "magnus.png"
            file_url = url_for("get_file", filename=filename)

            # Adds user to database
            cur.execute("INSERT INTO Account (username, password, profile_picture, permission_level, display_name, date) VALUES (?, ?, ?, 1, ?, ?)", (name, hashed_password, file_url, name, date))
            con.commit()

            session["user_id"] = cur.lastrowid # Auto logs in so user doesn't have to
            return redirect(url_for("home"))
        except sqlite3.IntegrityError:
            wtf_form.name.errors.append("That username is already taken")

    return render_template("register.html", form=wtf_form, header="Register")


@app.route("/uploads/<filename>")
def get_file(filename):
    # Gets the link directory of the file
    return send_from_directory(app.config["UPLOADED_PHOTOS_DEST"], filename)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    # Verifies login 
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password") 

        con = sqlite3.connect("climbing.db")
        cur = con.cursor()
        cur.execute("SELECT id, password FROM Account WHERE username = ?;", (username,))
        result = cur.fetchone()

        # Ensures user is in database
        if result:
            correct_password = result[1]
            if check_password_hash(correct_password, password):
                session["user_id"] = result[0]
                print(type(result[0]))
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
