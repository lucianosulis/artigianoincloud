from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

import getpass

bp = Blueprint('home', __name__)

@bp.route('/home')
@login_required
def index():
# Questo stamperà l'utente nel terminale non appena avvii l'applicazione
    print(f"--- L'APPLICAZIONE FLASK STA GIRANDO CON L'UTENTE: {getpass.getuser()} ---")
    return redirect('calendar')
    
