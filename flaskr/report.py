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
#import openpyxl
from openpyxl import Workbook, load_workbook
from openpyxl.styles import PatternFill, Border, Side, Font, Alignment 
from openpyxl.utils import get_column_letter
#from openpyxl.styles import Font
#from openpyxl.styles import Alignment
import io

bp = Blueprint('report', __name__)

@bp.route('/report', methods=('GET',))
@login_required
def index():
    if g.role != "ADMIN" and g.role != "SEGRETERIA":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("calendar.show_cal"))
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT o.id AS order_id, CONCAT(DATE_FORMAT(o.date,"%d/%m/%y"), " - ", c.full_name, " - ", REPLACE(o.description,"""","")) AS order_desc'
        ' FROM p_order o ' 
        ' INNER JOIN customer c ON o.customer_id = c.id ' 
        ' WHERE o.closed=0'
        ' ORDER BY c.full_name ASC, o.date DESC'
    )
    orders=cursor.fetchall()

    return render_template('report/index.html', orders=orders)

@bp.route('/report/order_activities', methods=['POST'])
def order_activities():
    # Recupero i parametri dal form della card
    #start = request.form.get('start')
    #end = request.form.get('end')
    order_id = request.form.get('order_id')
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT a.title AS Titolo, c.full_name AS Cliente, DATE_FORMAT(a.start,"%d/%m/%y") AS Data_inizio, DATE_FORMAT(a.end,"%d/%m/%y") AS Data_fine, s.address AS Indirizzo, s.city AS Città '
        ' FROM activity a ' 
        ' INNER JOIN p_order o ON o.id = a.p_order_id '
        ' INNER JOIN site s ON s.id = a.site_id '
        ' INNER JOIN customer c ON o.customer_id = c.id ' 
        ' WHERE o.closed=0 AND a.p_order_id = %s'
        ' ORDER BY c.full_name ASC, o.date DESC',(order_id,)
    )
    acts=cursor.fetchall()
    print(acts)
    excel_file = generate_excel_response(acts,sheet_name="Attività")
    if not excel_file:
        flash("Nessun dato trovato")
        return redirect(url_for('report.index')) # Torna alla pagina dei report
    return send_file(
            excel_file,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name="report_attivita.xlsx")

@bp.route('/report/order_teams', methods=['POST'])
def order_teams():
    # Recupero i parametri dal form della card
    #start = request.form.get('start')
    #end = request.form.get('end')
    order_id = request.form.get('order_id')
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT a.title AS Titolo, c.full_name AS Cliente, ' 
        ' DATE_FORMAT(a.start,"%d/%m/%y") AS Inizio_attività, ' 
        ' DATE_FORMAT(a.end,"%d/%m/%y") AS Fine_attività, s.address AS Indirizzo, s.city AS Città, '
        ' CONCAT(p.surname, " ",p.name) AS Operatore, DATE_FORMAT(t.date,"%d/%m/%y") AS Data'
        ' FROM activity a ' 
        ' INNER JOIN p_order o ON o.id = a.p_order_id '
        ' INNER JOIN site s ON s.id = a.site_id '
        ' INNER JOIN customer c ON o.customer_id = c.id ' 
        ' INNER JOIN rel_team_activity rta ON a.id = rta.activity_id '
        ' INNER JOIN team t ON t.id = rta.team_id '
        ' INNER JOIN rel_team_people rtp ON t.id = rtp.team_id '
        ' INNER JOIN people p ON p.id = rtp.people_id '
        ' WHERE o.closed=0 AND a.p_order_id = %s'
        ' ORDER BY c.full_name ASC, o.date DESC',(order_id,)
    )
    acts=cursor.fetchall()
    print(acts)
    excel_file = generate_excel_response(acts,sheet_name="Attività")
    if not excel_file:
        flash("Nessun dato trovato")
        return redirect(url_for('report.index')) # Torna alla pagina dei report
    return send_file(
            excel_file,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name="report_attivita.xlsx")

def generate_excel_response(query_results, sheet_name="Report"):
    print(query_results)
    if not query_results:
        return None
    print("OK")
    # Creo un nuovo workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Attività"
    ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
    #ws.row_dimensions[1].height = 25
    #ws.row_dimensions[2].height = 25
    #ws.column_dimensions['A'].width = 10  # Imposta la larghezza della colonna in caratteri
    #ws.column_dimensions['B'].width = 5 
    #ws.column_dimensions['AH'].width = 7
    # 3. Estrai le intestazioni dalle chiavi del primo dizionario
    headers = list(query_results[0].keys())
    ws.append(headers)
    # Styling opzionale: Intestazione in grassetto
    for cell in ws[1]:
        cell.font = Font(bold=True)

    for record in query_results:
        row_data = [record.get(key) for key in headers]
        ws.append(row_data) 
    #Adatto la larghezza delle colonne al contenuto
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter # Ottiene la lettera (A, B, C...)
        for cell in col:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))
        ws.column_dimensions[column].width = max_length + 2
    # 5. Salva in un buffer di memoria invece che su disco
    output = io.BytesIO()
    wb.save(output)
    output.seek(0) #Riavvolge "il nastro" all'inizio
    return output
        


