from flask import (
    Blueprint, flash, g, redirect, render_template, request, 
    url_for, current_app, jsonify, json, session, 
    send_from_directory)
from flask_paginate import Pagination, get_page_args, get_page_parameter
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db
from datetime import date
from datetime import datetime
from flaskr.fir import create_analog_fir
import os
from PIL import Image, ImageDraw, ImageFont, ImageOps

bp = Blueprint('activity', __name__)

@bp.route('/activity', methods=('GET', 'POST'))
@login_required
def index():
    session["show_calendar"] = 'N'
    # Recuperiamo l'URL da cui proviene l'utente
    referrer = request.referrer or ""
    # LOGICA DI RESET:
    # Se l'utente arriva da un'ALTRA pagina (es. menu principale)
    # e non è un invio di modulo (POST), allora vogliamo il posizionamento speciale.
    if request.method == 'GET' and "/activity" not in referrer:
        session["activity_first_page"] = 'Y'
    else:
        # Se sta già navigando dentro /activity (paginazione, filtri, ecc.)
        # o se ha cliccato esplicitamente su un numero di pagina
        session["activity_first_page"] = 'N'
    activity_first_page = session.get("activity_first_page","Y")
    
    current_app.config.from_file("config.json", load=json.load)
    per_page = current_app.config["FL_PER_PAGE"]
    db = get_db() 
    cursor = db.cursor(dictionary=True)
    #Creazione filtro
    current_year = date.today().year
    active_year = session.get("active_year",current_year)
    conditions = []
    params = []
    conditions.append("year = %s")
    params.append(f"{active_year}")
    searchStr = " WHERE " + " AND ".join(conditions)
    
    if request.method == 'GET':
        page = request.args.get('page', 1, type=int)
        conditions2 = session.get("act1_search_conditions2", [])
        params2 = session.get("act1_search_params2", [])
        search_date = session.get("act1_search_date","")
        search_customer = session.get("act1_search_customer","")
        search_site = session.get("act1_search_site","")
        if conditions2:
            searchStr = searchStr + " AND " + " AND ".join(conditions2)
            params = params + params2
    
    if request.method == 'POST': 
        page = 1
        search_date = request.form.get("searchDate","")
        search_customer = request.form.get("searchCustomer","")
        search_site = request.form.get("searchSite","")
        session["act1_search_date"] = search_date
        session["act1_search_customer"] = search_customer
        session["act1_search_site"] = search_site
        # 1. Inizializziamo una lista per le condizioni aggiuntive e una per i parametri
        conditions2 = []
        params2 = []
        if search_date:
            conditions2.append("start = %s")
            params2.append(f"{search_date}") 
        if search_customer:
            conditions2.append("full_name LIKE %s")
            params2.append(f"%{search_customer}%") # Il % lo mettiamo nel dato, non nella query
        if search_site:
            conditions2.append("CONCAT(site.city,' - ',site.address) LIKE %s")
            params2.append(f"%{search_site}%") # Il % lo mettiamo nel dato, non nella query
       
        # 2. Trasformiamo la lista di condizioni in una stringa da aggiungere alla clausola WHERE
        #searchStr = ""
        if conditions2:
            searchStr = searchStr + " AND " + " AND ".join(conditions2)
            params = params + params2
            
        #session["act1_search"] = searchStr
        session["act1_search_conditions2"] = conditions2
        session["act1_search_params2"] = params2

    count_query = ('SELECT COUNT(*) AS count FROM '
                ' (SELECT a.id, title, a.start AS start, a.end AS end, c.full_name AS customer, CONCAT(site.city," - ",site.address) AS site '
                ' FROM activity a'
                ' INNER JOIN p_order o ON a.p_order_id = o.id'
                ' INNER JOIN site ON a.site_id = site.id'
			    ' INNER JOIN customer c ON o.customer_id = c.id ' +
                searchStr + ") AS activities"
                )
    cursor.execute(count_query, params)
    total = cursor.fetchone()['count']
    offset = (page-1) * per_page 

    if activity_first_page == 'Y':
            #Si posiziona sull pagina più vicina al giorno di oggi
            today = date.today()
            search3Str = searchStr + ' AND start < %s'
            params3 = params + [today]
            count_query3 = ('SELECT COUNT(*) AS count FROM '
                ' (SELECT a.id, title, a.start AS start, a.end AS end, c.full_name AS customer, CONCAT(site.city," - ",site.address) AS site '
                ' FROM activity a'
                ' INNER JOIN p_order o ON a.p_order_id = o.id'
                ' INNER JOIN site ON a.site_id = site.id'
			    ' INNER JOIN customer c ON o.customer_id = c.id ' +
                search3Str + ") AS activities"
                )
            cursor.execute(count_query3,params3)
            rowCount3 = cursor.fetchone()
            number_to_bypass = rowCount3['count']   
            page_num = int((number_to_bypass / per_page)) + 1 
            offset = (int(page_num)-1) * per_page
            page = str(page_num) 
            session["activity_first_page"] = 'N'

    pagination = Pagination(page=page, per_page=per_page, total=total, 
                            css_framework='bootstrap4')

    final_query = ('SELECT a.id, title, DATE_FORMAT(a.start,"%d/%m/%y") AS start, DATE_FORMAT(a.end,"%d/%m/%y") AS end, c.full_name AS customer, CONCAT(site.city," - ",site.address) AS site'
             ' FROM activity a'
             ' INNER JOIN p_order o ON a.p_order_id = o.id'
             ' INNER JOIN site ON a.site_id = site.id'
			 ' INNER JOIN customer c ON o.customer_id = c.id' +
             searchStr +
            ' ORDER BY a.start ASC LIMIT %s OFFSET %s'
        )
    # Aggiungiamo LIMIT e OFFSET alla lista dei parametri esistenti
    final_params = params + [per_page, offset]
    cursor.execute(final_query, final_params)
    #print(f"final_query: {final_query}")
    #print(f"final_params: {final_params}")
    acts = cursor.fetchall() 
    
    return render_template('activity/index.html', acts=acts,pagination=pagination,search_date=search_date,search_customer=search_customer,search_site=search_site)

@bp.route('/activity/create', methods=('GET', 'POST'))
@login_required
def create():
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("activity.index"))
    orderList = get_orderList()
    #anag_tags = get_anag_tags()
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        start = request.form['start']
        start_obj = datetime.strptime(start, "%Y-%m-%d")
        year = start_obj.year
        end = request.form['end']
        order_id = request.form['order_id']
        site_id = request.form['input_site_id'] 
        tag_id = request.form.get('tag_id')
        
        error = None

        if (not start) or (not end) or (not order_id) or (not site_id):
            error = 'Compila tutti i campi obbligatori.'
        if start > end:
            error = 'La data di fine attività deve essere maggiore o uguale alla data di inizio .'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            #Se title è vuoto, lo imposto uguale alla descrizione dell'ordine
            if (not title):  
                cursor.execute('SELECT description FROM p_order WHERE id = %s', (order_id,))
                row = cursor.fetchone()
                title = row['description']
             #Creo il nuovo record per l'attività
            cursor.execute(
                'INSERT INTO activity (title, description, start, end, p_order_id, site_id, year)'
                ' VALUES (%s, %s, %s, %s, %s, %s, %s)',
                (title, description, start, end, order_id, site_id, year)
            )
            db.commit()

            cursor.execute('SELECT LAST_INSERT_ID() AS last_insert')
            row = cursor.fetchone()
            activity_id = row['last_insert']
            print(f"tag_id: {tag_id}")
            cursor.execute(
                'INSERT INTO rel_tag_activity (activity_id, tag_id)'
                ' VALUES (%s, %s)',
                (activity_id, tag_id)
            )
            db.commit()

            return redirect(url_for('activity.index'))

    return render_template('activity/create.html', orderList=orderList)

@bp.route('/activity/<sel_date>/create_from_cal', methods=('GET', 'POST'))
@login_required
def create_from_cal(sel_date):
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("activity.index"))
    orderList = get_orderList()

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        start = request.form['start']
        start_obj = datetime.strptime(start, "%Y-%m-%d")
        year = start_obj.year
        end = request.form['end']
        order_id = request.form['order_id']
        site_id = request.form['input_site_id']
        tag_id = request.form.get('tag_id')
    
        error = None 

        if (not start) or (not end) or (not order_id) or (not site_id):
            error = 'Compila tutti i campi obbligatori.'
        if start > end:
            error = 'La data di fine attività deve essere maggiore o uguale alla data di inizio .'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            #Se title è vuoto, lo imposto uguale alla descrizione dell'ordine
            if (not title):  
                cursor.execute('SELECT description FROM p_order WHERE id = %s', (order_id,))
                row = cursor.fetchone()
                title = row['description']
            #Creo il nuovo record per l'attività
            cursor.execute(
                'INSERT INTO activity (title, description, start, end, p_order_id, site_id, year)'
                ' VALUES (%s, %s, %s, %s, %s, %s, %s)',
                (title, description, start, end, order_id, site_id, year)
            )
            db.commit()

            cursor.execute('SELECT LAST_INSERT_ID() AS last_insert')
            row = cursor.fetchone()
            activity_id = row['last_insert']
            cursor.execute(
                'INSERT INTO rel_tag_activity (activity_id, tag_id)'
                ' VALUES (%s, %s)',
                (activity_id, tag_id)
            )
            db.commit()
            
            return redirect(url_for('calendar.show_cal'))

    return render_template('activity/create_from_cal.html',orderList=orderList,sel_date=sel_date)

@bp.route('/activity/create_wo_order', methods=('GET', 'POST'))
@login_required
def create_wo_order():
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("activity.index"))
    customerList = get_customerList()
    anag_tags = get_anag_tags()
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        start = request.form['start']
        start_obj = datetime.strptime(start, "%Y-%m-%d")
        year = start_obj.year
        end = request.form['end']
        customer_id = request.form['customer_id']
        site_id = request.form['input_site_id']
        tag_id = request.form.get('tag_id')
    
        error = None

        #current_app.logger.debug(str(start) + " - " + str(end) + " - " + str(site_id) + " - " + str(customer_id))
        if (not start) or (not end) or (not site_id) or (not customer_id) or (not tag_id):
            error = 'Compila tutti i campi obbligatori.'
        if start > end:
            error = 'La data di fine attività deve essere maggiore o uguale alla data di inizio .'

        if error is not None:
            flash(error)
        else:
            
            session["fc_call_type"] = "fc_new_order"
            session["customer_id"] = customer_id
            session["site_id"] = site_id
            session["title"] = title
            session["description"] = description
            session["start"] = start
            session["end"] = end
            session["notes"] = ""
            session['selected_tag'] = tag_id
            session["year"] = year
            return redirect('/oauth')

    return render_template('activity/create_wo_order.html', customerList=customerList, anag_tags=anag_tags)

@bp.route('/activity/<int:id>/create_from_order', methods=('GET', 'POST'))
@login_required
def create_from_order(id):
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("activity.index"))
    order = get_order_desc(id)
    order_desc = order['order_desc']
    order_tags = getOrderTags(id)
    #print(order_tags)

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        start = request.form['start']
        start_obj = datetime.strptime(start, "%Y-%m-%d")
        year = start_obj.year
        end = request.form['end']
        order_id = request.form['order_id']
        site_id = request.form['input_site_id']
        tag_id = request.form.get('tag_id')
        #tag_id = (tag or {}).get('tag_id')
    
        error = None

        if (not start) or (not end) or (not order_id) or (not site_id):
            error = 'Compila tutti i campi obbligatori.'
        if start > end:
            error = 'La data di fine attività deve essere maggiore o uguale alla data di inizio .'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            #Se title è vuoto, lo imposto uguale alla descrizione dell'ordine
            if (not title):  
                cursor.execute('SELECT description FROM p_order WHERE id = %s', (order_id,))
                row = cursor.fetchone()
                title = row['description']
            #Creo il nuovo record per l'attività
            cursor.execute(
                'INSERT INTO activity (title, description, start, end, p_order_id, site_id, year)'
                ' VALUES (%s, %s, %s, %s, %s, %s, %s)',
                (title, description, start, end, order_id, site_id, year)
            )
            db.commit()
            cursor.execute('SELECT LAST_INSERT_ID() AS last_insert')
            row = cursor.fetchone()
            activity_id = row['last_insert']
            cursor.execute(
                'INSERT INTO rel_tag_activity (activity_id, tag_id)'
                ' VALUES (%s, %s)',
                (activity_id, tag_id)
            )
            db.commit()
            return redirect(url_for('activity.index'))

    return render_template('activity/create_from_order.html', order_id=id, order_desc=order_desc, order_tags=order_tags)


@bp.route('/activity/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("activity.index"))
    if session.get("show_calendar","N")  == "N":
        redirect_url = url_for('activity.index')
    else:
        redirect_url = url_for('calendar.show_cal')
    act = get_act(id)
    order_id = act['p_order_id']
    order_desc = get_order(id)
    siteList = get_siteList(order_id)
    order_tags = getOrderTags(order_id)
    tag = get_act_tag(id)
    tag_id = (tag or {}).get('tag_id')
    materials_ls = get_act_materials(id)
    materials = json.dumps(materials_ls) #json

    if request.method == 'POST': 
        title = request.form['title']
        description = request.form['description']
        start = request.form['start']
        start_obj = datetime.strptime(start, "%Y-%m-%d")
        year = start_obj.year
        end = request.form['end']
        order_id = request.form['order_id']
        site_id = request.form['input_site_id']
        tag_id = request.form.get('tag_id')
        dati_json_stringa2 = request.form.get('dati_griglia_json2')
        current_app.logger.debug(dati_json_stringa2)
        dati_griglia2 = []
        if dati_json_stringa2:
            try:
                # Deserializza la stringa JSON in una lista di dizionari Python
                dati_griglia2 = json.loads(dati_json_stringa2)
                #print(dati_griglia2)
            except json.JSONDecodeError:
                print("Errore nella decodifica dei dati JSON della griglia 2")
                error = 'Errore nella decodifica dei dati JSON della griglia 2.'

        error = None

        if (not title) or (not start) or (not end) or (not order_id) or (not site_id):
            error = 'Compila tutti i campi obbligatori.'
        if start > end:
            error = 'La data di fine attività deve essere maggiore o uguale alla data di inizio.'
        
        if error is not None:
            flash(error)
        else:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                'UPDATE activity SET title = %s, description = %s, start = %s, end = %s, p_order_id = %s, site_id = %s, year = %s '
                ' WHERE id = %s',
                (title, description, start, end, order_id, site_id, year, id)
            )
            db.commit() 
            cursor.execute(
                'DELETE FROM rel_tag_activity '
                ' WHERE activity_id = %s ',
                (id,)
            )
            cursor.execute(
                'INSERT INTO rel_tag_activity (activity_id, tag_id) '
                ' VALUES (%s, %s)',
                (id,tag_id)
            )
            db.commit()

            cursor.execute(
                'DELETE FROM material_usage '
                ' WHERE activity_id = %s ',
                (id,)
            )
            print(f"dati_griglia2: {dati_griglia2}")
            for record in dati_griglia2:
                # 'record' è ora un singolo dizionario (es: {'act_type_id': 1, ...})
                # Estraggo i singoli campi da questo dizionario
                print(record)
                #act_id = record['activity_id']
                mat_desc = record['description']
                cost = record['cost']
                cursor.execute(
                    'INSERT INTO material_usage (description, activity_id, cost) '
                    ' VALUES (%s, %s, %s)',
                    (mat_desc, id, cost)
                )
            db.commit()
            return redirect(redirect_url)
    return render_template('activity/update.html', act=act, order_id=order_id, order_desc=order_desc, siteList=siteList, order_tags=order_tags, tag_id=tag_id, materials=materials,redirect_url=redirect_url)

@bp.route('/activity/<int:id>/duplicate', methods=('GET', 'POST'))
@login_required
def duplicate(id):
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("activity.index"))
    act = get_act(id)
    order_id = act['p_order_id']
    order_desc = get_order(id)
    siteList = get_siteList(order_id)
    order_tags = getOrderTags(order_id)
    tag = get_act_tag(id)
    tag_id = (tag or {}).get('tag_id')
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        start = request.form['start']
        start_obj = datetime.strptime(start, "%Y-%m-%d")
        year = start_obj.year
        end = request.form['end']
        order_id = request.form['order_id']
        site_id = request.form['input_site_id']
        
        error = None

        if (not title) or (not start) or (not end) or (not order_id) or (not site_id):
            error = 'Compila tutti i campi obbligatori.'
        if start > end:
            error = 'La data di fine attività deve essere maggiore o uguale alla data di inizio .'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                'INSERT INTO activity (title, description, start, end, p_order_id, site_id, year)'
                ' VALUES (%s, %s, %s, %s, %s, %s, %s)',
                (title, description, start, end, order_id, site_id, year)
            )
            db.commit()
            cursor.execute('SELECT LAST_INSERT_ID() AS last_insert')
            row = cursor.fetchone()
            activity_id = row['last_insert']
            print(f"tag_id: {tag_id}")
            cursor.execute(
                'INSERT INTO rel_tag_activity (activity_id, tag_id)'
                ' VALUES (%s, %s)',
                (activity_id, tag_id)
            )
            db.commit()
            
            return redirect(url_for('activity.index'))
    return render_template('activity/duplicate.html', act=act, order_id=order_id, order_desc=order_desc, siteList=siteList, order_tags=order_tags, tag_id=tag_id)

@bp.route('/activity/<int:id>/fir', methods=('GET', 'POST'))
@login_required
def fir(id):
    act = get_act(id)
    site = get_site(id)
    site_desc = site['site_desc']
    anag_waste_storages = get_anag_waste_storages()
    fir_date = act['end']
    anag_tractors = get_anag_tractors()
    anag_trailers = get_anag_trailers()

    if request.method == 'POST':
        fir_date_object = datetime.strptime(request.form['fir_date'], "%Y-%m-%d")
        fir_date = fir_date_object.strftime("%d/%m/%Y")
        waste_storage_id = request.form.get('waste_storage_id')
        waste_storage = get_waste_storage(waste_storage_id)
        tractor_id = request.form.get('tractor_id')
        trailer_id = request.form.get('trailer_id')
        tractor = get_tool(tractor_id)
        trailer = get_tool(trailer_id)
        site_desc = request.form['site_desc']
        weight = request.form['weight']
        prod_denom = "PRONTOGIARDINI S.R.L."
        prod_address = "Via San Cassiano 1 - 24030 Mapello (BG)"
        prod_cf = "04721650168"
        prod_iscr_n = "MI85294"
        prod_iscr_type = "Aut. integrata ambientale"
        dest_denom = waste_storage['company_name']
        dest_address = waste_storage['dest_address']
        dest_cf = waste_storage['codice_fiscale']
        dest_act = waste_storage['codice_attivita']
        dest_auth_n = waste_storage['n_autorizzazione']
        dest_auth_type = waste_storage['tipo_autorizzazione']
        trasp_denom = "PRONTOGIARDINI S.R.L."
        trasp_cf = "04721650168"
        trasp_iscr_n = "MI85294"
        license_plate_tractor = tractor['license_plate']
        license_plate_trailer = trailer['license_plate']
        driver_name = request.form['driver_name']
        transp_date_object = datetime.strptime(request.form['transp_date'], "%Y-%m-%d")
        transp_date = transp_date_object.strftime("%d/%m/%Y")
        transp_time = request.form['transp_time']
        
        error = None

        if (not fir_date) or (not waste_storage_id) or (not site_desc) or (not weight) or (not tractor_id) or (not trailer_id):
            error = 'Compila tutti i campi obbligatori.'

        if error is not None:
            flash(error)
        else:
            path,nome_file = create_analog_fir(
                fir_date,prod_denom,prod_address,prod_cf, 
                prod_iscr_n,prod_iscr_type,site_desc,dest_denom,dest_address,dest_cf,dest_act,dest_auth_n, 
                dest_auth_type,trasp_denom,trasp_cf,trasp_iscr_n,weight, 
                license_plate_tractor,license_plate_trailer,driver_name,transp_date,transp_time)

            return send_from_directory(path, nome_file, as_attachment=True)
            #return redirect(url_for('activity.index'))

    return render_template('activity/fir.html', fir_date=fir_date, site_desc=site_desc, 
                           anag_waste_storages=anag_waste_storages, anag_tractors=anag_tractors, anag_trailers=anag_trailers)


@bp.route('/activity/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("activity.index"))
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute('DELETE FROM rel_team_activity WHERE activity_id = %s', (id,))
    cursor.execute('DELETE FROM rel_tag_activity WHERE activity_id = %s', (id,))
    cursor.execute('DELETE FROM material_usage WHERE activity_id = %s', (id,))
    cursor.execute('DELETE FROM timesheet WHERE act_id = %s', (id,))
    cursor.execute('DELETE FROM tool_usage WHERE act_id = %s', (id,))
    cursor.execute('DELETE FROM activity WHERE id = %s', (id,))
    db.commit()
    return redirect(url_for('activity.index'))


@bp.route('/activity/<int:id>/detail', methods=('GET',))
@login_required
def detail(id):
    act = get_act(id)
    order = get_order(id)
    site = get_site(id)
    ts_people = get_ts_people(id)
    ts_total_hours = get_ts_total_hours(id)
    tu_tool = get_tu_tool(id)
    #anag_tags = get_anag_tags()
    tag = get_act_tag(id)
    #print(tag)
    fotos = get_fotos(id)
    numero_foto = len(fotos)
    materials = get_act_materials(id)
    if session.get("show_calendar","N")  == "N":
        redirect_url = url_for('activity.index')
    else:
        redirect_url = url_for('calendar.show_cal')
    return render_template('activity/detail.html', act=act, order=order, site=site, ts_people=ts_people, tu_tool=tu_tool, tag=tag, ts_total_hours=ts_total_hours, redirect_url=redirect_url, numero_foto=numero_foto, materials=materials)

@bp.route('/activity/<int:id>/gallery', methods=('GET',))
@login_required
def gallery(id):
    act = get_act(id)
    fotos = get_fotos(id)
    show_calendar = session["show_calendar"]
    return render_template('activity/gallery.html', act=act, fotos=fotos, show_calendar=show_calendar)

@bp.route("/sel_order", methods=('POST',))
@login_required
def sel_order():
    select = request.form.get('order')
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM 'order' ")
    orderList=cursor.fetchall()
    #current_app.logger.debug(orderList)
    return render_template("activity/sel_order.html",orderList=orderList )

@bp.route("/<int:order_id>/sel_site", methods=('POST',))
@login_required
def sel_site(order_id):
    results= get_siteList(order_id)
    return (results)

@bp.route("/<int:customer_id>/sel_site2", methods=('POST',))
@login_required
def sel_site2(customer_id):
    results= get_siteList2(customer_id)
    return (results)

@bp.route("/<int:order_id>/order_desc", methods=('POST',))
@login_required
def order_desc(order_id):
    #current_app.logger.debug("order_desc dice: " + str(order_id))
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute('SELECT description FROM p_order WHERE id = %s', (order_id,))
    row = cursor.fetchone()
    order_desc = row['description']
    result= order_desc
    
    return (result)

@bp.route('/activity/<int:id>/to_do', methods=('POST',))
@login_required
def to_do(id):
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("activity.index"))
    #current_app.logger.debug("to_do dice: " + str(id))
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'UPDATE activity SET done = False'
        ' WHERE id = %s',
        (id,)
    )
    db.commit()
    return "to_do"

@bp.route('/activity/<int:id>/done', methods=('POST',))
@login_required
def done(id):
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("activity.index"))
    #current_app.logger.debug("done dice: " + str(id))
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'UPDATE activity SET done = True'
        ' WHERE id = %s',
        (id,)
    )
    db.commit()
    return "done"

@bp.route("/<int:order_id>/get_order_tags", methods=('POST',))
@login_required
def get_order_tags(order_id):
    order_tags= getOrderTags(order_id)
    return (order_tags)

@bp.route('/activity/<int:id>/upload_foto', methods=('POST',))
@login_required
def upload_foto(id):
    #print("upload_foto")
    activity_id = id
    if 'image' not in request.files:
        return jsonify({"message": "Nessun file inviato"}), 400
    file = request.files['image']
    lat = request.form.get('lat')
    lon = request.form.get('lon')
    foto_notes = request.form.get('foto_notes')
    print(f"Note della foto: {foto_notes}")
    BASE_DIR = "/usr/local/ArtigianoInCloud"
    current_app.config.from_file("config.json", load=json.load)
    UPLOAD_FOLDER = current_app.config["UPLOAD_FOLDER"]
    # Creiamo un nome file univoco con timestamp del server
    filename = f"foto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    clic_date = datetime.now()
    marchia_foto(filepath, lat, lon, clic_date)
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'INSERT INTO foto (filename, latitude, longitude, date, notes, activity_id)'
                ' VALUES (%s, %s, %s, %s, %s, %s)',
                (filename, lat, lon, clic_date, foto_notes, activity_id)
    )
    db.commit()
    # Qui potresti salvare lat, lon e filename in un database (SQLite, PostgreSQL, ecc.)
    print(f"Salvata: {filename} | Lat: {lat} | Lon: {lon} | Ora JS: {clic_date}")

    return jsonify({
        "message": "Foto e dati GPS salvati correttamente!",
        "filename": filename
    }), 200


def get_act(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT a.id, a.title, a.description, a.start, a.end, a.done, a.p_order_id, o.description AS order_desc,' 
        ' a.site_id, c.id AS customer_id, c.full_name'
        ' FROM activity a INNER JOIN p_order o ON a.p_order_id = o.id '
        ' INNER JOIN customer c ON o.customer_id = c.id'
        ' WHERE a.id = %s',
        (id,)
    )
    act = cursor.fetchone()
    #current_app.logger.debug(act)
    if act is None:
        abort(404, f"activity id {id} non esiste.")

    return act

def get_orderList():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT o.id, o.description, c.full_name'
        ' FROM p_order o INNER JOIN customer c ON o.customer_id = c.id'
        ' WHERE o.closed=0'
        ' ORDER BY c.full_name ASC'
    )
    orderList=cursor.fetchall()

    if orderList is None:
        abort(404, f"orderList è vuota.")
    return orderList

def get_customerList():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT c.id, c.full_name, c.address, c.city'
        ' FROM customer c'
        ' ORDER BY c.full_name ASC'
    )
    customerList=cursor.fetchall()

    if customerList is None:
        abort(404, f"customerList è vuota.")
    return customerList

def get_order(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        ' SELECT CONCAT(c.full_name," - ",o.description," - ",DATE_FORMAT(o.date,"%d/%m/%Y") ) AS order_desc'
        ' FROM activity a '
        ' INNER JOIN p_order o ON a.p_order_id = o.id'
        ' INNER JOIN customer c ON o.customer_id = c.id'
        ' WHERE a.id = %s', (id,)
    )
    order=cursor.fetchone()
    return order

def get_order_desc(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        ' SELECT CONCAT(c.full_name," - ",o.description," - ",DATE_FORMAT(o.date,"%d/%m/%Y") ) AS order_desc'
        ' FROM p_order o '
        ' INNER JOIN customer c ON o.customer_id = c.id'
        ' WHERE o.id = %s', (id,)
    )
    order=cursor.fetchone()
    return order

def get_siteList(order_id):
    #current_app.logger.debug("get_siteList")
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT s.id, s.address, s.city, c.full_name'
        ' FROM p_order o INNER JOIN customer c ON o.customer_id = c.id'
        ' INNER JOIN site s ON c.id = s.customer_id'
        ' WHERE o.id = %s',
        (order_id,)
        )
    siteList=cursor.fetchall()
    if siteList is None:
        abort(404, f"siteList è vuota.")
    #current_app.logger.debug(siteList)
    return siteList

def get_siteList2(customer_id):
    #current_app.logger.debug("get_siteList2")
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT s.id, s.address, s.city, c.full_name'
        ' FROM customer c '
        ' INNER JOIN site s ON c.id = s.customer_id'
        ' WHERE c.id = %s',
        (customer_id,)
        )
    siteList=cursor.fetchall()

    if siteList is None:
        abort(404, f"siteList è vuota.")
    #current_app.logger.debug(siteList)
    return siteList

def get_site(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT CONCAT(s.city, " - ",s.address) AS site_desc'
        ' FROM activity a'
        ' INNER JOIN site s ON s.id = a.site_id'
        ' WHERE a.id = %s',
        (id,)
    )
    site=cursor.fetchone()
    return site

def get_ts_people(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT GROUP_CONCAT(ts.id) AS id, GROUP_CONCAT(DATE_FORMAT(ts.date,"%d/%m/%Y")) as date, GROUP_CONCAT(CONCAT(p.surname," ", p.name)) as p_name, GROUP_CONCAT(ts.ore_lav) as ore_lav'
             ' FROM activity a'
             ' INNER JOIN timesheet ts ON a.p_order_id = ts.order_id'
             ' INNER JOIN people p on ts.people_id = p.id'
             ' WHERE (ts.act_type_id = 1 OR ts.act_type_id = 6)'
             	' AND ts.date >= a.start AND ts.date <= end '
                ' AND a.id = %s',
                (id,)
    )
    ts_people = cursor.fetchone()
    return ts_people

def get_tu_tool(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT GROUP_CONCAT(tu.id) AS id, GROUP_CONCAT(DATE_FORMAT(tu.date,"%d/%m/%Y")) as date, GROUP_CONCAT(CONCAT(t.brand," ", t.model)) as t_name, GROUP_CONCAT(tu.ore_lav) as ore_lav'
             ' FROM activity a'
             ' INNER JOIN tool_usage tu ON a.p_order_id = tu.order_id'
             ' INNER JOIN tool t on tu.tool_id = t.id'
             ' WHERE tu.date >= a.start AND tu.date <= end '
                ' AND a.id = %s',
                (id,)
    )
    tu_tool = cursor.fetchone()
    return tu_tool

def get_anag_waste_storages():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT * FROM waste_storage '
             '  order by company_name ASC '
       )
    anag_waste_storages = cursor.fetchall()
    return anag_waste_storages

def get_waste_storage(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT id,company_name,CONCAT(address," - ",zip_code," - ",city) AS dest_address,' 
        'codice_fiscale,codice_attivita,n_autorizzazione,tipo_autorizzazione '
        ' FROM waste_storage WHERE id=%s',
        (id,)
       )
    waste_storage = cursor.fetchone()
    return waste_storage

def get_anag_tractors():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT id AS tool_id, CONCAT(brand," ",model," ",license_plate," ",serial_number) AS tool_name '
        ' FROM tool  WHERE (tool_type_id=10 OR tool_type_id=12 OR tool_type_id=15) '
        ' AND discontinued=0 ' 
        ' ORDER BY tool_name'
    )
    anag_tractors=cursor.fetchall()
    return anag_tractors

def get_anag_trailers():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT id AS tool_id, CONCAT(brand," ",model," ",license_plate," ",serial_number) AS tool_name '
        ' FROM tool  WHERE (tool_type_id=13 OR tool_type_id=14) ' 
        ' AND discontinued=0 '
        ' ORDER BY tool_name'
    )
    anag_trailers=cursor.fetchall()
    return anag_trailers

def get_tool(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT id, tool_type_id, brand, model, serial_number, license_plate, notes, discontinued' 
        ' FROM tool'
        ' WHERE id = %s AND discontinued=0',
        (id,)
    )
    tool = cursor.fetchone()
    return tool

def get_anag_tags():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT id AS tag_id, CONCAT(code," - ",description) AS tag_desc'
        ' FROM tag'
        ' ORDER BY code ASC'
    )
    tags=cursor.fetchall()

    if tags is None:
        abort(404, f"tags è vuota.")
    return tags

def get_act_tag(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT rta.tag_id,CONCAT(t.code," - ",t.description) AS tag_desc '
        ' FROM rel_tag_activity rta'
        ' INNER JOIN tag t ON t.id=rta.tag_id'
        ' WHERE activity_id = %s ',
        (id,)
    )
    tag=cursor.fetchone()
    return tag

def get_tool_typeList():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT id, type'
        ' FROM tool_type ORDER BY type ASC'
    )
    tool_typeList=cursor.fetchall()

    if tool_typeList is None:
        abort(404, f"tool_typeList è vuota.")
    return tool_typeList

def get_ts_total_hours(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT SUM(ore_lav) AS total_hours from timesheet '
        ' WHERE act_id=%s',(id,)
    )
    total_hours = cursor.fetchone()['total_hours']
    return total_hours

def getOrderTags(order_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT t.id AS tag_id, CONCAT(t.code," - ",t.description) AS tag_desc'
        ' FROM tag t' 
        ' INNER JOIN rel_tag_order rto ON rto.tag_id=t.id '
        ' WHERE rto.p_order_id=%s'
        ' ORDER BY t.code ASC',(order_id,)
    )
    order_tags=cursor.fetchall()
    if order_tags is None:
        abort(404, f"order_tags è vuota.")
    return order_tags

def marchia_foto(path, lat, lon, clic_date):
    print("marchia_foto")
    try:
        img = Image.open(path).convert("RGB") # Forza RGB per evitare problemi con JPG/PNG
        #img = Image.open(path)
        img = ImageOps.exif_transpose(img) # Ruota l'immagine fisicamente in base ai metadati
        draw = ImageDraw.Draw(img)
        # 1. Calcola una dimensione font proporzionale (es. 5% dell'altezza immagine)
        width, height = img.size
        font_size = int(height * 0.03) 
        # 2. Carica un font (Arial o DejaVu sono standard su Ubuntu)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except:
            font = ImageFont.load_default() # Fallback se il font non esiste
        testo = f"Pos: {lat}, {lon} \n Data: {clic_date.strftime('%d/%m/%Y %H:%M')}"
        # Scegli una posizione (es. in basso a destra)
        #draw.text((10, 10), testo, fill=(255, 255, 255)) # Testo bianco
        # 3. Posizionamento (in basso a sinistra, con un po' di margine)
        margin = 20
        # draw.text((x, y), ...)
        draw.text((margin, height - font_size * 2 - margin), testo, fill=(255, 255, 0), font=font) # Giallo è più visibile
        img.save(path)
        return True # Tutto ok!
    except Exception as e:
        print(f"Errore: {e}")
        return False # Qualcosa è andato storto

# Questa rotta "legge" fisicamente il file dal disco di Ubuntu
@bp.route('/download_foto/<filename>')
@login_required
def download_foto(filename):
    print(f"filename: {filename}")
    # Usiamo current_app.config per prendere il percorso definito in __init__.py
    current_app.config.from_file("config.json", load=json.load)
    UPLOAD_FOLDER = current_app.config["UPLOAD_FOLDER"]
    print(f"UPLOAD_FOLDER: {UPLOAD_FOLDER}")
    return send_from_directory(UPLOAD_FOLDER, filename)

def get_fotos(act_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT f.id,f.filename,f.latitude,f.longitude,f.date,f.notes '
        ' FROM foto f'
        ' INNER JOIN activity a ON a.id=f.activity_id '
        ' WHERE a.id=%s '
        ' ORDER BY f.date ASC',(act_id,)
    )
    fotos=cursor.fetchall()

    if fotos is None:
        abort(404, f"fotos è vuota.")
    return fotos

def get_act_materials(act_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT * FROM material_usage '
        ' WHERE activity_id=%s ',(act_id,)
    )
    materials=cursor.fetchall()
    if materials is None:
        abort(404, f"materials è vuota.")
    return materials