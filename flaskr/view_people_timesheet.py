from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app, jsonify, json, session
)
from flask_paginate import Pagination, get_page_args, get_page_parameter
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db
from flask import send_file, send_from_directory

from datetime import datetime, timedelta
import calendar
from dateutil.easter import *

bp = Blueprint('view_people_timesheet', __name__)

@bp.route('/view_people_timesheet', methods=('GET', 'POST'))
@login_required
def index():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        ' select p.id as people_id from people p '
        ' inner join user u on p.user_id = u.id '
        ' where u.id=%s',(g.user_id,) 
    )
    row = cursor.fetchone()
    try:
        people_id = row['people_id']
    except: 
        flash("Questo utente non è in anagrafica del personale.")
        return redirect(url_for('home.index'))
    session["activity_first_page"] = 'Y'

    hours_dict = {}
    hours_dict['OreLavDiurne'] = 0
    hours_dict['OreLavNotturne'] = 0
    hours_dict['OreFerie'] = 0
    hours_dict['OreMalattia'] = 0
    hours_dict['OrePNR'] = 0
    hours_dict['OrePR'] = 0
    hours_dict['OreMaltempo'] = 0
    hours_dict['OreTotali'] = 0

    if request.method == 'POST': 
        input = request.form['month'] 
        
        error = None
        if (not input):
            error = 'Compila il mese/anno.'
        if error is not None:
            flash(error)
        else:
            yearStr = input.split('-')[0]
            year = int(yearStr)
            monthStr = input.split('-')[1]
            month = int(monthStr)
            last_month_day = calendar.monthrange(year,month)[1]
            last_month_dayStr = str(last_month_day)
            start_date = yearStr + "-" + monthStr + "-" + "01"
            end_date = yearStr + "-" + monthStr + "-" + last_month_dayStr
            db = get_db()
            cursor = db.cursor(dictionary=True)
            
            cursor.execute(
                ' SELECT people_id, SUM(ore_lav) AS ore '
                ' FROM timesheet t '
                ' inner join act_type at on t.act_type_id = at.id '
                ' WHERE people_id = %s AND t.date >= %s AND t.date <= %s '
                ' and at.short_code = "LAV" and t.night = false '
                ' GROUP BY people_id ',
                (people_id, start_date, end_date)
            )
            hours = cursor.fetchone()
            try:
                hours_dict['OreLavDiurne'] = hours['ore']
            except:
                hours_dict['OreLavDiurne'] = 0
            
            cursor.execute(
                ' SELECT people_id, SUM(ore_lav) AS ore '
                ' FROM timesheet t '
                ' inner join act_type at on t.act_type_id = at.id '
                ' WHERE people_id = %s AND t.date >= %s AND t.date <= %s '
                ' and at.short_code = "LAV" and t.night = true '
                ' GROUP BY people_id ',
                (people_id, start_date, end_date)
            )
            hours = cursor.fetchone()
            try:
                hours_dict['OreLavNotturne'] = hours['ore']
            except:
                hours_dict['OreLavNotturne'] = 0
            
            cursor.execute(
                ' SELECT people_id, SUM(ore_lav) AS ore '
                ' FROM timesheet t '
                ' inner join act_type at on t.act_type_id = at.id '
                ' WHERE people_id = %s AND t.date >= %s AND t.date <= %s '
                ' and at.short_code = "FE" '
                ' GROUP BY people_id ',
                (people_id, start_date, end_date)
            )
            hours = cursor.fetchone()
            try:
                hours_dict['OreFerie'] = hours['ore']
            except:
                hours_dict['OreFerie'] = 0

            cursor.execute(
                ' SELECT people_id, SUM(ore_lav) AS ore '
                ' FROM timesheet t '
                ' inner join act_type at on t.act_type_id = at.id '
                ' WHERE people_id = %s AND t.date >= %s AND t.date <= %s '
                ' and at.short_code = "M" '
                ' GROUP BY people_id ',
                (people_id, start_date, end_date)
            )
            hours = cursor.fetchone()
            try:
                hours_dict['OreMalattia'] = hours['ore']
            except:
                hours_dict['OreMalattia'] = 0

            cursor.execute(
                ' SELECT people_id, SUM(ore_lav) AS ore '
                ' FROM timesheet t '
                ' inner join act_type at on t.act_type_id = at.id '
                ' WHERE people_id = %s AND t.date >= %s AND t.date <= %s '
                ' and at.short_code = "PNR" '
                ' GROUP BY people_id ',
                (people_id, start_date, end_date)
            )
            hours = cursor.fetchone()
            try:
                hours_dict['OrePNR'] = hours['ore']
            except:
                hours_dict['OrePNR'] = 0

            cursor.execute(
                ' SELECT people_id, SUM(ore_lav) AS ore '
                ' FROM timesheet t '
                ' inner join act_type at on t.act_type_id = at.id '
                ' WHERE people_id = %s AND t.date >= %s AND t.date <= %s '
                ' and at.short_code = "PR" '
                ' GROUP BY people_id ',
                (people_id, start_date, end_date)
            )
            hours = cursor.fetchone()
            try:
                hours_dict['OrePR'] = hours['ore']
            except:
                hours_dict['OrePR'] = 0

            cursor.execute(
                ' SELECT people_id, SUM(ore_lav) AS ore '
                ' FROM timesheet t '
                ' inner join act_type at on t.act_type_id = at.id '
                ' WHERE people_id = %s AND t.date >= %s AND t.date <= %s '
                ' and at.short_code = "CISOA" '
                ' GROUP BY people_id ',
                (people_id, start_date, end_date)
            )
            hours = cursor.fetchone()
            try:
                hours_dict['OreMaltempo'] = hours['ore']
            except:
                hours_dict['OreMaltempo'] = 0

            #hours_dict['OreTotali'] = hours_dict['OreLavDiurne'] + hours_dict['OreLavNotturne'] + hours_dict['OreFerie'] + hours_dict['OreMalattia'] + hours_dict['OrePNR'] + hours_dict['OrePR'] + hours_dict['OreMaltempo']
            #Solo le ore lavorative
            hours_dict['OreTotali'] = hours_dict['OreLavDiurne'] + hours_dict['OreLavNotturne']

    return render_template('view_people_timesheet/index.html',hours_dict = hours_dict)
    