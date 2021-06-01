import argparse
import csv
import osmium
import shapely.wkb as wkblib

wkbfab = osmium.geom.WKBFactory()

class Handler(osmium.SimpleHandler):
    def __init__(self,writer):
        super(Handler, self).__init__()
        self.writer = writer

    def area(self,a):
        try:
            if 'boundary' in a.tags:
                wkb = wkbfab.create_multipolygon(a)
                multipolygon = wkblib.loads(wkb, hex=True)
                self.writer.writerow([a.tags.get('name'),multipolygon.wkt])
        except RuntimeError as e:
            print("Error:",a.orig_id())

def main():
    parser = argparse.ArgumentParser(description='Create a protoshapes archive from an osm file.')
    parser.add_argument('osm_file',  help='OSM .pbf or .xml input file')
    parser.add_argument('output',  help='output file')
    parsed = parser.parse_args()

    with open(parsed.output, 'w') as csvfile:
        writer = csv.writer(csvfile, delimiter='\t')
        writer.writerow(["name","WKT"])
        h = Handler(writer)
        h.apply_file(parsed.osm_file, locations=True, idx='sparse_file_array')
