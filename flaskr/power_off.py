import subprocess
#from flask import Flask, render_template, request, jsonify, abort
from flask import (
    Blueprint, flash, g, redirect, render_template, request, 
    url_for, current_app, jsonify, json, session, 
    send_from_directory)
from flask_paginate import Pagination, get_page_args, get_page_parameter
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

# NOTA: Assicurati che questa pagina/rotta sia protetta da autenticazione!
bp = Blueprint('power_off', __name__)
@login_required
@bp.route('/power_off')
def index():
    return render_template('power_off/index.html')

@bp.route('/power_off', methods=['POST'])
def shutdown_server():
    if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("calendar.show_cal"))
    # Sicurezza: Accetta solo richieste POST
    if request.method == 'POST':
        try:
            # Esegue il comando in modo asincrono per permettere a Flask 
            # di rispondere al client prima che il server si spenga effettivamente.
            subprocess.Popen(['sudo', 'shutdown', 'now'])
            
            return jsonify({"status": "success", "message": "Il server si sta spegnendo..."}), 200
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
    else:
        abort(405)