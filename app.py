#! /usr/bin/env python

from __future__ import print_function
from functools import wraps
from flask import Flask, request, render_template, send_from_directory, Response, abort, make_response
import requests
from ics import Calendar
import ics.alarm
from fnmatch import fnmatch
from dotenv import load_dotenv, find_dotenv
import os
import datetime


load_dotenv(find_dotenv())
__SECRET__ = os.environ["EVENTSPEC_SECRET"]
__USER__ = os.environ["AUTHUSER"]
__PASS__ = os.environ["AUTHPASS"]
__TIMEOUT__ = 10

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
    try:
        r = requests.get(url, timeout=__TIMEOUT__)
    except requests.exceptions.ReadTimeout:
        return make_response("Indico upstream did not answer", 503)
        # abort(503)
    icsdata = r.text

    try:
        c = Calendar(icsdata) 
    except:
        return make_response("Error parsing ics data", 500)
    
    outc = Calendar()

    res = ""
    
    white = request.args.get("white").split(";")
    black = request.args.get("black").split(";")
    alerts = request.args.get("alerts")
    alerts = alerts.split(";") if alerts != None else [15]

    f = lambda s: len(s) > 0
    white = filter(f, white)
    black = filter(f, black)


    for e in c.events:
        if len(white) > 0 and not any(fnmatch(e.name, p) for p in white):
            continue
        if len(black) > 0 and any(fnmatch(e.name, p) for p in black):
            continue
        
        for alert in alerts:
            a = ics.alarm.DisplayAlarm(description=e.name, trigger=datetime.timedelta(minutes=int(alert)))
            e.alarms.append(a)

        outc.events.add(e)

    return str(outc)

# @app.route("/static/<path:path>")
# def statics(path=None):
    # return ""
    # return send_from_directory("static", path)

@app.route("/status")
def status():
    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ["PORT"]))
