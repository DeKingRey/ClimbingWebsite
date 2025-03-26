"""Docstring Climbing Website
A climbing flask website to aid climbers to find climbs and communicate
By Miguel Monreal on 27/03/25"""

from flask import Flask

app = Flask(__name__)


@app.route("/")
def Home():
    return None


if __name__ == "__main__":
    app.run(debug=True)
