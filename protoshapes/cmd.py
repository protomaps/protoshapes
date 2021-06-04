import argparse
import math
import sqlite3
import time
import os
import osmium
import shapely.wkb as wkblib
from rtree import index

wkbfab = osmium.geom.WKBFactory()

# https://taginfo.openstreetmap.org/keys/boundary#values
boundary_values = [
    'administrative',
    'protected_area',
    'political',
    'national_park',
    'census',
    'maritime',
    'neighborhood',
    'neighbourhood',
    'special_economic_zone',
    'regional_park',
    'state_park',
    'place',
    'tourist_zone',
    'statistical',
    'political_fraction',
    'local_authority',
    'local',
    'environment',
    'civil',
    'municipality'
]

def rad(degree):
    return degree * math.pi / 180

def geodesic_ring_area(ring):
    area = 0
    for i in range(len(ring)-1):
        p1 = ring[i]
        p2 = ring[i+1]
        area += rad(p2[0] - p1[0]) * (2 + math.sin(rad(p1[1])) + math.sin(rad(p2[1])))
    return -1 * area * 6378137.0 * 6378137.0 / 2.0

def geodesic_exterior_area(mp):
    area = 0
    for polygon in mp:
        area += geodesic_ring_area(polygon.exterior.coords)
    return area

class Handler(osmium.SimpleHandler):
    def __init__(self,conn,cursor,idx):
        super(Handler, self).__init__()
        self.conn = conn
        self.cursor = cursor
        self.idx = idx

    def area(self,a):
        try:
            if 'name' in a.tags and a.tags.get('boundary') in boundary_values:
                wkb = wkbfab.create_multipolygon(a)
                multipolygon = wkblib.loads(wkb, hex=True)
                area = geodesic_exterior_area(multipolygon)
                if area > 50000:
                    # prefix = 'w' if a.from_way() else 'r'
                    self.cursor.execute("INSERT INTO features_original VALUES (?,?,?,?,?,?)",(a.id,a.tags.get("name"),a.tags.get("boundary"),a.tags.get("admin_level"),area,multipolygon.wkb))
                    self.conn.commit()
                    self.idx.insert(a.id,multipolygon.bounds)
        except RuntimeError as e:
            print("Error:",a.orig_id())

EPSG4326 = '''GEOGCS["WGS 84",
    DATUM["WGS_1984",
        SPHEROID["WGS 84",6378137,298.257223563,
            AUTHORITY["EPSG","7030"]],
        AUTHORITY["EPSG","6326"]],
    PRIMEM["Greenwich",0,
        AUTHORITY["EPSG","8901"]],
    UNIT["degree",0.0174532925199433,
        AUTHORITY["EPSG","9122"]],
    AUTHORITY["EPSG","4326"]]'''

def main():
    parser = argparse.ArgumentParser(description='Create a protoshapes archive from an osm file.')
    parser.add_argument('osm_file',  help='OSM .pbf or .xml input file')
    parser.add_argument('output',  help='output sqlite')
    parsed = parser.parse_args()

    if os.path.exists(parsed.output):
        os.remove(parsed.output)

    conn = sqlite3.connect(parsed.output)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS spatial_ref_sys (srid integer unique, auth_name text, auth_srid integer, srtext text);')
    cursor.execute("INSERT INTO spatial_ref_sys VALUES (?,?,?,?)",(0,"epsg",4326,EPSG4326))
    cursor.execute('CREATE TABLE IF NOT EXISTS geometry_columns (f_table_name text, f_geometry_column text, geometry_type integer, coord_dimension integer, srid integer, geometry_format text);')
    cursor.execute("INSERT INTO geometry_columns VALUES (?,?,?,?,?,?)",("features_original","wkb_geometry",6,2,0,"WKB"))
    cursor.execute('CREATE TABLE IF NOT EXISTS features_original (id integer PRIMARY KEY, name text, boundary text, admin_level integer, area integer, wkb_geometry blob);')

    # populate the initial table of geometries
    idx = index.Index()
    start = time.time()
    h = Handler(conn,cursor,idx)
    h.apply_file(parsed.osm_file, locations=True, idx='sparse_file_array')
    conn.close()

    # populate spatial fields

    print("Elapsed: ", time.time() - start)
