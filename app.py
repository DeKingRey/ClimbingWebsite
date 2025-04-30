"""Docstring Climbing Website
A climbing flask website to aid climbers to find climbs and communicate
By Miguel Monreal on 27/03/25"""

from flask import Flask, render_template, redirect, url_for, send_from_directory, request, session\

from flask_bcrypt import Bcrypt, check_password_hash
from flask_uploads import UploadSet, IMAGES, configure_uploads
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms.validators import DataRequired, Length, EqualTo, Optional
from wtforms import StringField, PasswordField, SubmitField

import sqlite3
import requests


app = Flask(__name__)
# This secret key is required for Flask-WTF to protect against CSRF attacks
app.config["SECRET_KEY"] = "&^V*&OEB*@P(#DNUOE)"
# This sets the destination for uploaded photos to the 'uploads' folder 
app.config["UPLOADED_PHOTOS_DEST"] = "uploads"

bcrypt = Bcrypt(app)

# This is the variable which will hold the correct file type for images, getting the IMAGES variable which holds file types like png, jpg, gif, etc. It makes an upload set which is something which only allows certain file types(which is defined with the second parameter)
photos = UploadSet("photos", IMAGES)
# This configured the upload sets to the app, so will add previously defined 'photos' as one of the upload sets for this app
configure_uploads(app, photos)


# This creates a class which can be used to make forms(specifically for accounts)
class RegisterForm(FlaskForm):
    # Creates the name field which has to have input to be valid
    name = StringField("Name", validators=[DataRequired("Field should not be empty")])
    # Creates a password field which can't be empty and has to be at least 8 characters long
    password = PasswordField("Password", validators=[
        DataRequired("Field should not be empty"), 
        Length(min=8, message="Password should be at least 8 characters long")
        ])
    # Confirms that the user inputed the correct password by checking if it's the same as the previously defined Password
    confirm_password = PasswordField("Confirm_Password", validators=[EqualTo("password", "Passwords are not matching")])
    # Creates a file field where the profile picture can be uploaded
    photo = FileField(
        validators= [
            # Only allows the file types in the 'photos' upload set
            FileAllowed(photos, "Only images allowed"),
            # Is optional so the field can be empty and other errors will be ignored
            Optional()
        ]
    )

    # Creates the submit button which will check and validate the inputted data
    submit = SubmitField("Register")

# This is the url which is for the API
# Currently the API does not work so I will wait through the holidays to see if it continues to be like this
map_routes_url = "https://climbnz.org.nz/api/routes"


@app.route("/")
def home():
    user_id = session.get("user_id")
    
    if user_id is not None:
        con = sqlite3.connect("climbing.db")
        cur = con.cursor()
        cur.execute("SELECT profile_picture, username FROM Account WHERE id = ?", (user_id,))
        result = cur.fetchone()
        profile_picture = result[0]
        username = result[1]

        session["profile_picture"] = profile_picture
        session["username"] = username
    else:
        profile_picture = None
        username = None

    return render_template("home.html", header="Home", profile_picture=profile_picture, username=username)
    

# The climbing API I need to use is currently not working so I may need to come up with a workaround to this if it isn't fixed
@app.route("/map")
def map():
    
    return render_template("map.html", header="Map", profile_picture=session.get("profile_picture"), username=session.get("username"))


@app.route("/posts", methods=["GET", "POST"])
def posts():
    return render_template("posts.html", header="Posts", profile_picture=session.get("profile_picture"), username=session.get("username"))


@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        logout()
        return redirect(url_for("home"))
    return render_template("account.html", header="Account", profile_picture=session.get("profile_picture"), username=session.get("username"))


@app.route("/register", methods=["GET", "POST"])
def register():
    con = sqlite3.connect("climbing.db")
    cur = con.cursor()
    
    form = RegisterForm()

    if form.validate_on_submit():
        name = form.name.data
        password = form.password.data
        
        # This hashes the password making it secure and able to be stored in a database. Hashed things cannot be unhashed so it is quite secure
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        # This saves the photos file in the uploads folder
        if form.photo.data != None:
            # This saves the file in the uploads folder and gets the filename
            filename = photos.save(form.photo.data)
        else:
            # Guest Profile Picture
            # If there is no photo input then the users profile picture will be set to the guest profile picture
            filename = "magnus.png"
        # This will get the files url from the get_file() function
        file_url = url_for("get_file", filename=filename)

        # This executes an SQL stament which adds the users registry information to the database
        cur.execute("INSERT INTO Account (username, password, profile_picture) VALUES (?, ?, ?)", (name, hashed_password, file_url))
        con.commit()
        cur.close()
        return redirect(url_for("register"))
    return render_template("register.html", form=form, header="Register", profile_picture=session.get("profile_picture"), username=session.get("username"))


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

    return render_template("login.html", header="Login", error=error, profile_picture=session.get("profile_picture"), username=session.get("username"))


def logout():
    session["user_id"] = None
    session["profile_picture"] = None
    session["username"] = None

if __name__ == "__main__":
    app.run(debug=True)
