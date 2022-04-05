# Protoshapes

## Goals 
This project doesn't work yet. The goal is to create simplified polygons for places, such as administrative areas like cities or states, with a few special properties:

* Available for download in "1K" and "100K" versions, where the size of the geometry is guaranteed to be less than 1 or 100 kilobytes, respectively. 
  * This makes it practical to fetch and display any geometry in a web browser.
* Every point in the original geometry must be in the interior of the 1K or 100K geometry. That is, it is not a naive simplification which might cut away some of the area, but an expansion of the original area.
  * This property makes it useful as an efficient clipping boundary, since point-in-polygon algorithms are O(number of points).
* Maritime outer rings ought to be simplified via convex hull joining, but this should not happen for true exclaves.
* Contains a representative point for labeling, not necessarily the centroid.

## Non-goals

Geometries are designed to be worked with individually, and not for display together in something like a choropleth, because adjacent polygons will overlap when simplified. For that use case you should use [TopoJSON](https://github.com/topojson/topojson) or another kind of quantization-based technique.

## Workflow

Prepare your PBF file:

    osmium tags-filter -o planet-boundary.osm.pbf planet.osm.pbf r/boundary
    create-protoshapes planet-boundary.osm.pbf protoshapes-planet.csv
    ogr2ogr -f flatgeobuf protoshapes-planet.fgb protoshapes-planet.csv

## See also
* [Betashapes](https://github.com/simplegeo/betashapes)
* [Zetashapes](https://github.com/blackmad/zetashapes)
* [Quattroshapes](http://quattroshapes.com)
* [Mesoshapes](https://www.mapzen.com/blog/mesoshapes/)
* [Cosmogony](https://github.com/osm-without-borders/cosmogony)
* [osm-boundaries](https://github.com/missinglink/osm-boundaries)

