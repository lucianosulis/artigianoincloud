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

bp = Blueprint('cal_order', __name__)

@bp.route('/cal_order/<int:id>/cal', methods=('GET',))
@login_required
def cal(id):
    session["activity_first_page"] = 'Y'
    session["maintenance_first_page"] = 'Y'
    session["show_calendar"] = 'Y'
    db = get_db()
    cursor = db.cursor(dictionary=True)
    """
    if request.method == "POST": 
        #current_app.logger.debug(request.form)
        date_start = request.form['date_start']
        date_end = request.form['date_end']
        event_title = request.form['event_title']

        # store event to database
        cursor.execute("INSERT INTO activity (start, end, title, order_id, site_id) VALUES (%s, %s, %s, %s, %s)", 
                   (date_start, date_end, event_title, 1, 1))
        db.commit()

        # ajax
        if date_start and date_end and event_title:
           return jsonify({'start':date_start, 'end':date_end, 'title':event_title})
        return jsonify({'error' : 'Missing data!'})
    """
    cursor.execute('SELECT a.id, a.start, a.end, CONCAT(c.full_name," ",a.title) AS title, o.order_type, a.done'  
                    ' FROM activity a INNER JOIN p_order o ON a.p_order_id = o.id' 
                    ' INNER JOIN customer c ON o.customer_id = c.id'
                    ' WHERE o.id = %s' ,(id,))
    
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
        if row["done"] == 0:
            if row["order_type"] == "spot":
                d["backgroundColor"] = "#0086b3" #spot da fare: azzurro
            else:
                d["backgroundColor"] = "#009933"  #continuativo da fare: verde
        else:
            d["backgroundColor"] = "#992600" #fatto: rosso
        events_list.append(d)
        #current_app.logger.debug("d:")
        #current_app.logger.debug(d)
    #current_app.logger.debug(events_list)
    return render_template("order/cal_order.html", events = events_list)

# update event
@bp.route("/calendar/update", methods=("GET", "POST"))
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
    cursor.execute("UPDATE activity SET start = %s, end = %s WHERE id = %s", 
               (r["event[start]"],r["event[end]"],r["event[id]"],))
    db.commit()
    return redirect(url_for("calendar.show_cal"))

# delete event
#@bp.route("/delete", methods=("GET", "POST")) # methods=を消すとなぜかバグる(403)
#def delete_event(): 
#    r = request.form
    # delete event from db
#    db = get_db()
#    db.execute("DELETE FROM activity WHERE id = ? AND user_id = ?", 
#              (request.form["id"], session["user_id"]))
#    db.commit()
#    return redirect(url_for("calendar.show_cal"))