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

bp = Blueprint('cal_team_planned', __name__)

@bp.route("/cal_team_planned", methods=("GET", "POST"))
@login_required
def show_cal(): 
    session["show_calendar"] = 'Y'
    session["team_first_page"] = 'Y'
    db = get_db()
    cursor = db.cursor(dictionary=True)
    if request.method == "POST": 
        date_start = request.form['date_start']
        date_end = request.form['date_end']
        event_title = request.form['event_title']

        # ajax
        if date_start and date_end and event_title:
           return jsonify({'start':date_start, 'end':date_end, 'title':event_title})
        return jsonify({'error' : 'Dati mancanti!'})
    
    #cursor.execute('select id,date,title as name, "1" AS planned from team ' )
    cursor.execute('select distinct t.id,t.date,t.title as name, IF(r.activity_id is null, "2", "1") AS planned from team t '
                    ' left join rel_team_activity r on r.team_id = t.id ')
    events_rows = cursor.fetchall()
    #print("events_rows prima:")
    #print(events_rows)
    cursor.execute('select distinct date from team')
    dates = cursor.fetchall()
    for riga in dates:
        data = riga["date"]
        cursor.execute('SELECT p.id as id, %s AS date, CONCAT(p.surname," ",p.name) AS name, "0" AS planned '
                        ' FROM people p WHERE id NOT IN ( '
                        ' select p.id  from people p '
                        ' left JOIN rel_team_people r ON p.id = r.people_id '
                        ' left join team te on r.team_id = te.id '
                        ' where te.date = %s ) '
                        ' and id not in (select p.id from people p inner join timesheet t on p.id = t.people_id where date = %s and t.act_type_id > 1 and t.ore_lav >= 7 ) '
                        ' and p.cessato=0 and (p.type="D") ',
                        (data,data, data)
                        )
        result_set = cursor.fetchall()
        events_rows.extend(result_set)

        cursor.execute('SELECT pa.start, pa.end,p.id as id, %s AS date, CONCAT(p.surname," ",p.name) AS name, "0" AS planned '
                        ' FROM people p '
                        ' inner join people_available pa on pa.people_id = p.id '
                        ' WHERE %s >= pa.start and %s <= pa.end '
                        ' and p.id NOT IN ( '
                        '    select p.id  from people p '
                        '    left JOIN rel_team_people r ON p.id = r.people_id '
                        '    left join team te on r.team_id = te.id '
                        '    where te.date = %s ) ' 
                        ' and p.cessato=0 and (p.type="P" or p.type="C") ',
                        (data,data,data,data)
                        )
        result_set = cursor.fetchall()
        events_rows.extend(result_set)
    #print("events_rows dopo extend:")
    #print(events_rows)
    events_list = []
    color0 = "#0086b3"
    color1 = "#026D25"
    color2 = "#CE1D1DDF"
    
    for i in range(len(events_rows)):
        row = events_rows[i]
        team_id = row["id"]
        d = collections.OrderedDict()
        d["id"] = row["id"]
        d["title"] = row["name"] 
        d["classNames"] = "id-" + str(row["id"])
        if (row["planned"] == "1" or row["planned"] == "2"):
            d["url"] = "../team/" + str(row["id"]) + "/detail"
        else:
            d["url"] = "../people/" + str(row["id"]) + "/detail"
        date = row["date"]
        try:
            date_formatted = date.strftime("%Y-%m-%d")
            d["start"] = date_formatted
            d["end"] = date_formatted
        except:
            if len(date) < 10:
                date = get_filled_date(date)
            d["start"] = date
            d["end"] = date

        if row["planned"] == "0":
            d["backgroundColor"] = color0 
        elif row["planned"] == "1":
            d["backgroundColor"] = color1
        elif row["planned"] == "2":            
            d["backgroundColor"] = color2
        events_list.append(d)

    return render_template("cal_team_planned/cal_team_planned.html", events = events_list)

def get_filled_date(date_to_fill):
    date_to_fill_arr = date_to_fill.split("-")
    year = date_to_fill_arr[0]
    month = date_to_fill_arr[1].zfill(2)
    day = date_to_fill_arr[2].zfill(2)
    filled_date = year + "-" + month + "-" + day
    #print(filled_date)
    return filled_date