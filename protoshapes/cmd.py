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

def osm_id(fid):
    if fid % 2 == 0:
        return f"way/{int(fid/2)}"
    return f"relation/{int((fid-1)/2)}"

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
    return int(area)

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
                admin_level = a.tags.get("admin_level")
                area = geodesic_exterior_area(multipolygon)
                if area > 50000:
                    self.cursor.execute("INSERT INTO features_original(id,name,boundary,admin_level,area,wkb_geometry) VALUES (?,?,?,?,?,?)",(a.id,a.tags.get("name"),a.tags.get("boundary"),a.tags.get("admin_level"),area,multipolygon.wkb))
                    self.conn.commit()
                    if admin_level and int(admin_level) in [2,3,4,5,6,7,8,9,10]:
                        self.idx.insert(a.id,multipolygon.bounds,obj=int(admin_level))
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
    cursor.execute('CREATE TABLE IF NOT EXISTS features_original (id integer PRIMARY KEY, name text, boundary text, admin_level integer, area integer, wkb_geometry blob, a2 integer, a3 integer, a4 integer, a5 integer, a6 integer, a7 integer, a8 integer, a9 integer, a10 integer);')

    # populate the initial table of geometries
    idx = index.Index()
    start = time.time()
    h = Handler(conn,cursor,idx)
    h.apply_file(parsed.osm_file, locations=True, idx='sparse_file_array')

    # populate spatial fields
    subcursor = conn.cursor()
    for row in cursor.execute('SELECT id, area, wkb_geometry FROM features_original ORDER BY area DESC'):
        fid = row[0] 
        area = row[1]
        multipolygon = wkblib.loads(row[2])
        intersections = [(i.id,i.object) for i in idx.intersection(multipolygon.bounds,objects=True) if (i.id != fid)]
        candidates = [v[0] for v in sorted(intersections,key=lambda x:x[1])]
        within = [None,None,None,None,None,None,None,None,None]
        while len(candidates) > 0:
            candidate = candidates.pop(0)
            subcursor.execute("SELECT admin_level,wkb_geometry,a2,a3,a4,a5,a6,a7,a8,a9,a10 FROM features_original WHERE id = ?",(candidate,))
            candidate_row = subcursor.fetchone()
            candidate_poly = wkblib.loads(candidate_row[1])
            candidate_admins = candidate_row[2:11]
            admin_level = candidate_row[0]
            if multipolygon.within(candidate_poly):
                # if within[admin_level-2]:
                #     print(osm_id(fid),"in",osm_id(within[admin_level-2]),"or",osm_id(candidate))
                within[admin_level-2] = candidate
                for i in range(admin_level+1,11):
                    if candidate_admins[i-2]:
                        within[i-2] = candidate_admins[i-2]
                        candidates.remove(candidate_admins[i-2])
        subcursor.execute("UPDATE features_original SET a2=?, a3=?,a4=?,a5=?,a6=?,a7=?,a8=?,a9=?,a10=? WHERE id = ?",within + [fid])
        conn.commit()

    print("Elapsed: ", time.time() - start)
    conn.close()
