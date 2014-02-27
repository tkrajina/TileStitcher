import pdb

import logging as mod_logging
import tilestitcher as mod_tilestitcher
import gpxpy as mod_gpx

mod_logging.basicConfig(level=mod_logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')

gpx = mod_gpx.parse(open('example_files/track.gpx'))

gpx.reduce_points(100)

points = []
for point in gpx.walk(only_points=True):
    points.append((point.latitude, point.longitude,))

lat_1, lat_2, lon_1, lon_2 = gpx.get_bounds()
slipy_map = mod_tilestitcher.SlippyMapTiles(nth_best_zoom=0)
image = slipy_map.get_image((lat_1, lat_2), (lon_1, lon_2), 200, 200, \
                            polyline=points, polyline_color=(255, 0, 0))
image.show()

lat_1, lat_2, lon_1, lon_2 = gpx.get_bounds()
slipy_map = mod_tilestitcher.SlippyMapTiles(nth_best_zoom=1)
image = slipy_map.get_image((lat_1, lat_2), (lon_1, lon_2), 200, 200, \
                            polyline=points, polyline_color=(255, 0, 0))
image.show()
