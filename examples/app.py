import os
import json
import sys
import sqlite3
import shapely.wkb as wkblib
from shapely.geometry import mapping
from flask import current_app, g, Flask, jsonify, send_from_directory

app = Flask(__name__)

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            os.environ['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

app.teardown_appcontext(close_db)

@app.route("/")
def index():
    return send_from_directory('.','index.html')

@app.route('/shape/<shape_id>')
def get_shape(shape_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT wkb_geometry,a2,a3,a4,a5,a6,a7,a8,a9,a10,admin_level from features_original where id = ?",(shape_id,))
    row = cursor.fetchone()
    parents = []
    children = []
    for key in ['a2','a3','a4','a5','a6','a7','a8','a9','a10']:
        parents.append(row[key])
    if row['admin_level']:
        query = f"SELECT id from features_original where a{row['admin_level']} = ?"
        results = cursor.execute(query,(int(shape_id),))
        for result in results:
            children.append(result['id'])
    mp = wkblib.loads(row['wkb_geometry'])
    return jsonify({'geometry':mapping(mp),'type':'Feature','properties':{'parents':parents,'children':children}})
