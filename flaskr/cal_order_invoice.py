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

bp = Blueprint('cal_order_invoice', __name__)

@bp.route("/cal_order_invoice", methods=("GET", "POST"))
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
        if date_start and date_end and event_title:
           return jsonify({'start':date_start, 'end':date_end, 'title':event_title})
        return jsonify({'error' : 'Missing data!'})
    
    # GET: take out events and pass to calendar object
    cursor.execute('SELECT i.id, i.order_id, i.date, i.amount, i.invoiced, o.description, c.full_name'
            ' FROM po_invoices i'
            ' INNER JOIN p_order o ON i.order_id = o.id '
            ' INNER JOIN customer c ON o.customer_id = c.id '
			)
    events_rows = cursor.fetchall()
    events_list = []
    for row in events_rows: 
        d = collections.OrderedDict()
        d["id"] = row["order_id"]
        d_start = row["date"]
        d_end = row["date"]
        d["title"] = row["full_name"] + " " + row["description"]
        d["classNames"] = "id-" + str(row["id"])
        d["start"] = d_start.strftime("%Y-%m-%d")
        d["end"] = d_end.strftime("%Y-%m-%d")
        if row["invoiced"] == 0:
            d["backgroundColor"] = "#992600" #da fatturare: rosso
        else:
            d["backgroundColor"] = "#0086b3" #fatturata: azzurro
        events_list.append(d)
    return render_template("order/cal_order_invoice.html", events = events_list, )
