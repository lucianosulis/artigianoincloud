import mysql.connector
from flask import current_app, g
import json

def get_db():
    if 'db' not in g:
        current_app.config.from_file("config.json", load=json.load)
        g.db = mysql.connector.connect(
                                host=current_app.config["MYSQL_HOST"], port=current_app.config["MYSQL_PORT"],database=current_app.config["MYSQL_DB"],
                                user=current_app.config["MYSQL_USER"], password=current_app.config["MYSQL_PASSWORD"])
    #print("is_connected: " + str(g.db.is_connected()))
    return g.db

def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_app(app):
    app.teardown_appcontext(close_db)
