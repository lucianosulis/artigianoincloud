import functools
import re
import json
import collections
from datetime import datetime, timedelta

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, request, jsonify, current_app
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db
from flaskr.auth import login_required

bp = Blueprint('cal_availability', __name__)

@bp.route("/cal_availability", methods=("GET", "POST"))
@login_required
def show_cal():
    session["show_calendar"] = 'Y'
    db = get_db()
    cursor = db.cursor(dictionary=True)
    if request.method == "POST": 
        date_start = request.form['date_start']
        date_end = request.form['date_end']
        event_title = request.form['event_title']

        # store event to database
        cursor.execute("INSERT INTO people_available (start, end, people_id) VALUES (%s, %s, %s)", 
                   (date_start, date_end, event_title, 1, 1))
        db.commit()

        # ajax
        if date_start and date_end and event_title:
           return jsonify({'start':date_start, 'end':date_end, 'title':event_title})
        return jsonify({'error' : 'Missing data!'})
    
    # GET: take out events and pass to calendar object
    cursor.execute('SELECT pa.id, pa.start, pa.end, CONCAT(p.surname," ",p.name) AS title'  
                    ' FROM people_available pa ' 
                    ' INNER JOIN people p ON pa.people_id = p.id')
    events_rows = cursor.fetchall()
    events_list = []
    for row in events_rows: 
        d = collections.OrderedDict()
        d["id"] = row["id"]
        d_start = row["start"]
        d_end = row["end"]
        d["title"] = row["title"]
        d["classNames"] = "id-" + str(row["id"])
        if d_end > d_start:
            #FullCalendar richiede l'aggiunta di un giorno ad un evento multiday rispetto alla data effettiva da DB, altrimenti lo fa vedere più corto di uno.
            #date_old = datetime.strptime(d["end"], "%Y-%m-%d")
            date_old = d_end
            date_new = date_old + timedelta(days=1)
            #d["end"] = date_new.strftime("%Y-%m-%d")
            d_end = date_new
        d["start"] = d_start.strftime("%Y-%m-%d")
        d["end"] = d_end.strftime("%Y-%m-%d")
        d["backgroundColor"] = "#0086b3"
        events_list.append(d)
    #current_app.logger.debug(events_list)
    return render_template("cal_availability/cal.html", events = events_list)

# update event
@bp.route("/cal_availability/update", methods=("GET", "POST"))
@login_required
def update_event():  
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("cal_availability.show_cal"))
    #current_app.logger.debug("Update!")
    r = request.form
    # update event object
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("UPDATE people_available SET start = %s, end = %s WHERE id = %s", 
               (r["event[start]"],r["event[end]"],r["event[id]"],))
    db.commit()
    return redirect(url_for("cal_availability.show_cal"))
