import pdb

import tilestitcher as mod_tilestitcher
import gpxpy as mod_gpx

gpx = mod_gpx.parse(open('example_files/track.gpx'))

gpx.reduce_points(100)

points = []
for point in gpx.walk(only_points=True):
    points.append(point)

lat_1, lat_2, lon_1, lon_2 = gpx.get_bounds()
print lat_1, lat_2, lon_1, lon_2

slipy_map = mod_tilestitcher.SlippyMapTiles()
image = slipy_map.get_image((lat_1, lat_2), (lon_1, lon_2), 200, 200, \
                            polyline=points, polyline_color=(255, 0, 0))

image.show()
