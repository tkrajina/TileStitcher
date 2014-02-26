# TileStitcher

Python library to stitch and crop [OpenStreetMap](http://www.openstreetmap.org/) tiles.

## Usage

Create a 200x200 pixels image of an area between latitues (45.2775, 46.3785) and longitudes (13.5261, 14.9271):

    slipy_map = mod_tilestitcher.SlippyMapTiles()
    image = slipy_map.get_image((45.2775, 46.3785), (13.5261, 14.9271), 200, 200)
    image.show()

The library will try to find the needed tiles and the best zoom, stitch them and crop to cover the needed area.

The resulting image is a [PIL](http://pythonware.com/products/pil/) Image object.

Note that bigger images will need more tiles. By default the library is limited to stitch 2 tiles horizontally and 2 vertically. If you need more (but keep in mind the OSM tile usage policy!):

    slipy_map = mod_tilestitcher.SlippyMapTiles(max_tiles=3)

If you plan not to use the best zoom, but the second best zoom (one level smaller):

    slipy_map = mod_tilestitcher.SlippyMapTiles(nth_best_zoom=1)

## TODO

 * Waypoints

## License

TileStitcher is licensed under the [Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0)

Check the [OSM tile usage policy](http://www.openstreetmap.org). Most importantly display the license distribution and *do not* use this library for bulk downloading!
