import pdb

import tilestitcher as mod_tilestitcher
import gpxpy as mod_gpx

gpx = mod_gpx.parse(open('example_files/track.gpx'))

gpx.reduce_points(30)

points = []
for point in gpx.walk(only_points=True):
    points.append(point)

lat_1, lat_2, lon_1, lon_2 = gpx.get_bounds()
print lat_1, lat_2, lon_1, lon_2

slipy_map_tilenames = mod_tilestitcher.SlippyMapTilenames()
print slipy_map_tilenames.get_image((lat_1, lat_2), (lon_1, lon_2), 400, 400, polyline=points)
