# Protoshapes

Protoshapes is a free polygon dataset of named places, currently boundaries, derived from OpenStreetMap. It is designed to be fast and flexible to generate. 

The input format is an [OSM Express](https://github.com/protomaps/OSMExpress) database. The conversion step takes 30-40 minutes with minimal RAM requirements on a single computer. 

## Downloads

[Link to download](https://downloads.protomaps.com/files/protoshapes_20220406.fgb.zst) - 2.29 GB, 584043 features

* The dataset (`protoshapes.fgb.zst`) is a [Zstandard](http://facebook.github.io/zstd/)-compressed indexed FlatGeobuf. You will need the `zstd` decompressor to extract the data.
* All downloads carry the same license as OSM, The [Open Database License](http://openstreetmap.org/copyright)

## Workflow

    osmx-protoshapes planet.osmx protoshapes_unindexed.fgb
    ogr2ogr -f FlatGeobuf protoshapes.fgb protoshapes_unindexed.fgb
    tippecanoe -o protoshapes.mbtiles protoshapes.fgb -l protoshapes --drop-densest-as-needed

## Future Goals 

* Construct an admin_level hierarchy based on spatial relationships.
* Generalizations in "1K" and "100K" versions, where the size of the geometry is guaranteed to be less than 1 or 100 kilobytes, which makes geometry practical to fetch and display on the web. Every point in the original geometry should be in the interior of the 1K or 100K geometry. That is, it is not a naive simplification which might cut away some of the area, but an expansion of the original area. This property makes it useful as an efficient clipping boundary.
* Maritime outer rings ought to be simplified via convex hull joining, but this should not happen for true exclaves.
* Contain a representative point for labeling (pole of inaccessibility), not necessarily the centroid.

## Non-goals

* Geometries are designed to be worked with individually, and not for display together in something like a choropleth, because adjacent polygons will overlap when simplified. For that use case you should use [TopoJSON](https://github.com/topojson/topojson) or another kind of quantization-based technique.
* Does not interpret OSM admin_levels in an opinionated way.
* Not a geocoder or reverse geocoder, but useful as information to augment geocoding results. 

## See also
* [Betashapes](https://github.com/simplegeo/betashapes)
* [Zetashapes](https://github.com/blackmad/zetashapes)
* [Quattroshapes](http://quattroshapes.com)
* [Mesoshapes](https://www.mapzen.com/blog/mesoshapes/)
* [Cosmogony](https://github.com/osm-without-borders/cosmogony)
* [osm-boundaries](https://github.com/missinglink/osm-boundaries)

