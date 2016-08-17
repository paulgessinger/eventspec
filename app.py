#! /usr/bin/env python

from __future__ import print_function
from functools import wraps
from flask import Flask, request, render_template, send_from_directory, Response
import requests
from ics import Calendar
from fnmatch import fnmatch
from dotenv import load_dotenv, find_dotenv
import os


load_dotenv(find_dotenv())
__SECRET__ = os.environ["EVENTSPEC_SECRET"]
__USER__ = os.environ["AUTHUSER"]
__PASS__ = os.environ["AUTHPASS"]


app = Flask(__name__)

def check_auth(username, password):
    return username == __USER__ and password == __PASS__

def authenticate():
    return Response("Auth needed", 401, {"WWW-Authenticate": "Basic realm=\"Login\""})

def authed(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def valid_secret(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not request.args.get("secret") == __SECRET__:
            return Response("Forbidden", 403)
        return f(*args, **kwargs)
    return decorated

@app.route("/")
@authed
def index():
    return render_template("enter.html", secret=__SECRET__)

@app.route("/ics")
@valid_secret
def get_ics():
    url = request.args.get("url")
    r = requests.get(url)
    icsdata = r.text
    c = Calendar(icsdata) 
    
    outc = Calendar()

    res = ""
    
    white = request.args.get("white").split(";")
    black = request.args.get("black").split(";")

    f = lambda s: len(s) > 0
    white = filter(f, white)
    black = filter(f, black)


    for e in c.events:
        if len(white) > 0 and not any(fnmatch(e.name, p) for p in white):
            continue
        if len(black) > 0 and any(fnmatch(e.name, p) for p in black):
            continue
        outc.events.append(e)

    return str(outc)

@app.route("/static/<path:path>")
def statics(path=None):
    print("STATIC", path)
    return ""
    # return send_from_directory("static", path)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ["PORT"]))
