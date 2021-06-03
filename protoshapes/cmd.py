import argparse
import csv
import osmium
import shapely.wkb as wkblib
from shapely.ops import transform
import dbm
import math
import pyproj

wkbfab = osmium.geom.WKBFactory()

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
    def __init__(self,writer):
        super(Handler, self).__init__()
        self.writer = writer

    def area(self,a):
        try:
            if 'boundary' in a.tags:
                if a.tags['boundary'] in ['administrative','state_park','national_park','census','political','neighbourhood','place']:
                    wkb = wkbfab.create_multipolygon(a)
                    multipolygon = wkblib.loads(wkb, hex=True)
                    if geodesic_exterior_area(multipolygon) > 50000:
                        prefix = 'w' if a.from_way() else 'r'
                        self.writer.writerow([f"{prefix}{a.orig_id()}",a.tags.get('name'),a.tags.get('boundary'),multipolygon.wkt])
                elif a.tags['boundary'] in ['protected_area','aboriginal_lands','religious_administration','wall','native_reservation',"fire_district"]:
                    pass
                else:
                    print(a.orig_id(),a.tags['boundary'])
        except RuntimeError as e:
            print("Error:",a.orig_id())

def main():
    parser = argparse.ArgumentParser(description='Create a protoshapes archive from an osm file.')
    parser.add_argument('osm_file',  help='OSM .pbf or .xml input file')
    parser.add_argument('output',  help='output file')
    parsed = parser.parse_args()

    with open(parsed.output, 'w') as csvfile:
        writer = csv.writer(csvfile, delimiter='\t')
        writer.writerow(["osm_id","name","boundary","WKT"])
        h = Handler(writer)
        h.apply_file(parsed.osm_file, locations=True, idx='sparse_file_array')
