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

bp = Blueprint('cal_holidays', __name__)

@bp.route("/cal_holidays", methods=("GET", "POST"))
@login_required
def show_cal(): 
    session["show_calendar"] = 'Y'
    session["activity_first_page"] = 'Y'
    db = get_db()
    cursor = db.cursor(dictionary=True)
    if request.method == "POST": 
        #current_app.logger.debug(request.form)
        date_start = request.form['date_start']
        date_end = request.form['date_end']
        event_title = request.form['event_title']

        # ajax
        if date_start and date_end and event_title:
           return jsonify({'start':date_start, 'end':date_end, 'title':event_title})
        return jsonify({'error' : 'Dati mancanti!'})
    
    cursor.execute('select t.id, t.date, CONCAT(p.surname," ",p.name) AS people_name, at.short_code  '
                   ' from timesheet t ' 
                   ' inner join people p on p.id = t.people_id '
                   ' inner join act_type at on at.id = t.act_type_id '
                    ' where t.act_type_id >= 2 and t.act_type_id <= 5 and p.cessato = 0 ' )
    events_rows = cursor.fetchall()
    events_list = []
    for row in events_rows: 
        d = collections.OrderedDict()
        d["id"] = row["id"]
        d_start = row["date"]
        d_end = row["date"]
        d["title"] = row["people_name"] + " - " + row["short_code"]
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
        d["backgroundColor"] = "#0086b3" #azzurro
        events_list.append(d)
        #current_app.logger.debug("d:")
        #current_app.logger.debug(d)
    #current_app.logger.debug(events_list)
    return render_template("cal_holidays/cal_holidays.html", events = events_list)

# update event
'''@bp.route("/cal_holidays/update", methods=("GET", "POST"))
@login_required
def update_event(): 
    current_app.logger.debug("Update!")
    r = request.form
    current_app.logger.debug("event parameters:")
    current_app.logger.debug(r["event[start]"])
    current_app.logger.debug(r["event_old[start]"])
    current_app.logger.debug(r["event[end]"])
    current_app.logger.debug(r["event[id]"])
    # update event object
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("UPDATE timesheet SET date = %s WHERE id = %s", 
               (r["event[start]"],r["event[id]"],))
    db.commit()
    return redirect(url_for("cal_holidays.show_cal"))'''
