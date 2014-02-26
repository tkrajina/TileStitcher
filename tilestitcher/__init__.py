# -*- coding: utf-8 -*-

# Copyright 2014 Tomo Krajina
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pdb

import logging as mod_logging
import cStringIO as mod_stringio
import collections as mod_collections
import math as mod_math
import requests as mod_requests
import Image as mod_image
import ImageDraw as mod_imagedraw
import ImageFont as mod_imagefont

class TileInfo:
    def __init__(self, x, y, zoom):
        self.x = x
        self.y = y
        self.zoom = zoom

    def __str__(self):
        return 'Tile(x=%s, y=%s, zoom=%s)' % (self.x, self.y, self.zoom)

    def get_tile_url(self):
        x = self.x
        y = self.y

        n = 2 ** self.zoom
        if x < 0:
            x += n
        if y < 0:
            y += n
        if x >= n:
            x -= n;
        if y >= n:
            y -= n

        return 'http://tile.openstreetmap.org/%s/%s/%s.png' % (self.zoom, int(x), int(y))

# All the data needed to stitch and crop an image:
ImageInfo = mod_collections.namedtuple(
        'ImageInfo',
        ('tile_1', 'tile_2', 'widthheight_window_1', 'widthheight_window_2', 'latlon_window_1', 'latlon_window_2', 'center_x', 'center_y'))

class SlippyMapTiles:
    def __init__(self, max_tiles=None, nth_best_zoom=None):
        self.min_zoom = 0
        self.max_zoom = 19
        self.tile_size = 256

        # max tiles to stitch
        self.max_tiles = max_tiles or 2

        # When computing the best zoom 0 means the best one, 1 the the second best...
        self.nth_best_zoom = nth_best_zoom or 0

    def _deg2num(self, lat_deg, lon_deg, zoom, leave_float=False):
        """ Taken from http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Python """
        lat_rad = mod_math.radians(lat_deg)
        n = 2.0 ** zoom
        xtile = (lon_deg + 180.0) / 360.0 * n
        ytile = (1.0 - mod_math.log(mod_math.tan(lat_rad) + (1 / mod_math.cos(lat_rad))) / mod_math.pi) / 2.0 * n
        if not leave_float:
            xtile = int(xtile)
            ytile = int(ytile)
        return TileInfo(xtile, ytile, zoom)

    def _num2deg(self, tile):
        """ Taken from http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Python """
        n = 2.0 ** tile.zoom
        lon_deg = tile.x / n * 360.0 - 180.0
        lat_rad = mod_math.atan(mod_math.sinh(mod_math.pi * (1 - 2 * tile.y / n)))
        lat_deg = mod_math.degrees(lat_rad)
        return (lat_deg, lon_deg)

    def _get_position_on_stitched_image(self, tile_1, tile_2, latitude, longitude):
        assert tile_1.x <= tile_2.x
        assert tile_1.y <= tile_2.y
        assert tile_1.zoom == tile_2.zoom
        
        zoom = tile_1.zoom
        tile = self._deg2num(latitude, longitude, zoom, leave_float=True)
        return self.tile_size * (tile.x - int(tile_1.x)), self.tile_size * (tile.y - int(tile_1.y))

    def _get_best_zoom_data(self, center, latitute_range, longitude_range, width, height):
        candidates = []
        for zoom in range(self.min_zoom, self.max_zoom):
            # Find tile:
            center_tile = self._deg2num(center[0], center[1], zoom, leave_float=True)
            location_on_image = (self.tile_size * (center_tile.x - int(center_tile.x)), self.tile_size * (center_tile.y - int(center_tile.y)))

            # Check how many tiles left/right/bottop/up are needed:
            left   = location_on_image[0] - width / 2.
            right  = location_on_image[0] + width / 2.
            top    = location_on_image[1] - height / 2.
            bottom = location_on_image[1] + height / 2.

            left_tiles, right_tiles, top_tiles, bottom_tiles = 0, 0, 0, 0
            if left < 0:
                left_tiles = 1 + int(abs(left) / 256.)
            if right > self.tile_size:
                right_tiles = 1 + int((right - self.tile_size) / self.tile_size)
            if bottom > self.tile_size:
                bottom_tiles = 1 + int((bottom - self.tile_size) / self.tile_size)
            if top < 0:
                top_tiles = 1 + int(abs(top) / 256.)

            # Tile bounds:
            tile_1 = TileInfo(int(center_tile.x) - left_tiles,  int(center_tile.y) - top_tiles, zoom)
            tile_2 = TileInfo(int(center_tile.x) + right_tiles, int(center_tile.y) + bottom_tiles, zoom)
            assert tile_1.x <= tile_2.x
            assert tile_1.y <= tile_2.y
            assert tile_1.zoom == tile_2.zoom

            if tile_2.x - tile_1.x + 1 <= self.max_tiles and tile_2.y - tile_1.y + 1 <= self.max_tiles:
                center_x, center_y = self._get_position_on_stitched_image(tile_1, tile_2, center[0], center[1])

                # There are now two windows on the image. One is given by 
                # lat/lon bounds, and the other with width, height. Every 
                # window can be represented with two points The lat/lon window 
                # must be *inside* the width/height window:
                latlon_window_1 = self._get_position_on_stitched_image(tile_1, tile_2, latitute_range[0], longitude_range[0])
                latlon_window_2 = self._get_position_on_stitched_image(tile_1, tile_2, latitute_range[1], longitude_range[1])

                widthheight_window_1 = (center_x - width / 2., center_y - height / 2.)
                widthheight_window_2 = (center_x + width / 2., center_y + height / 2.)

                mod_logging.debug('lat/lon bounds: ' + str(latlon_window_1))
                mod_logging.debug('lat/lon bounds: ' + str(latlon_window_2))
                mod_logging.debug('width/height bounds: ' + str(widthheight_window_1))
                mod_logging.debug('width/height bounds: ' + str(widthheight_window_2))

                latlon_inside_widthheight =     widthheight_window_1[0] <= latlon_window_1[0] <= widthheight_window_2[0] \
                                            and widthheight_window_1[0] <= latlon_window_2[0] <= widthheight_window_2[0] \
                                            and widthheight_window_1[1] <= latlon_window_2[1] <= widthheight_window_2[1] \
                                            and widthheight_window_1[1] <= latlon_window_2[1] <= widthheight_window_2[1]

                if latlon_inside_widthheight:
                    candidates.append(ImageInfo(tile_1, tile_2, widthheight_window_1, widthheight_window_2, \
                                       latlon_window_1, latlon_window_2, center_x, center_y))

        if not candidates:
            return None

        candidates.reverse()

        n = self.nth_best_zoom
        if n >= len(candidates):
            n = -1

        result = candidates[n]
        mod_logging.debug('zoom=%s' % result.tile_1.zoom)
        return result

    def get_image(self, latitute_range, longitude_range, width, height, polyline=None, polyline_color=None, \
                  polyline_width=None, attribution=None):
        assert len(latitute_range) == 2
        assert latitute_range[0] < latitute_range[1]
        assert len(longitude_range) == 2
        assert longitude_range[0] < longitude_range[1]

        center = ((latitute_range[0] + latitute_range[1]) / 2., (longitude_range[0] + longitude_range[1]) / 2.)

        image_info = self._get_best_zoom_data(center, latitute_range, longitude_range, width, height)

        if not image_info:
            return None

        stitched = self._stitch_tiles(image_info.tile_1, image_info.tile_2, self.tile_size)

        """ DEBUG:
        draw = mod_imagedraw.Draw(stitched) 
        draw.ellipse((image_info.center_x - 2, image_info.center_y - 2, image_info.center_x + 2, image_info.center_y + 2), fill=(0, 0, 0))

        red = (255, 0, 0)
        draw.ellipse((image_info.widthheight_window_1[0] - 2, image_info.widthheight_window_1[1] - 2, image_info.widthheight_window_1[0] + 2, image_info.widthheight_window_1[1] + 2), fill=red)
        draw.ellipse((image_info.widthheight_window_2[0] - 2, image_info.widthheight_window_2[1] - 2, image_info.widthheight_window_2[0] + 2, image_info.widthheight_window_2[1] + 2), fill=red)
        draw.ellipse((image_info.widthheight_window_1[0] - 2, image_info.widthheight_window_2[1] - 2, image_info.widthheight_window_1[0] + 2, image_info.widthheight_window_2[1] + 2), fill=red)
        draw.ellipse((image_info.widthheight_window_2[0] - 2, image_info.widthheight_window_1[1] - 2, image_info.widthheight_window_2[0] + 2, image_info.widthheight_window_1[1] + 2), fill=red)

        blue = (0, 0, 255)
        draw.ellipse((image_info.latlon_window_1[0] - 2, image_info.latlon_window_1[1] - 2, image_info.latlon_window_1[0] + 2, image_info.latlon_window_1[1] + 2), fill=blue)
        draw.ellipse((image_info.latlon_window_2[0] - 2, image_info.latlon_window_2[1] - 2, image_info.latlon_window_2[0] + 2, image_info.latlon_window_2[1] + 2), fill=blue)
        draw.ellipse((image_info.latlon_window_1[0] - 2, image_info.latlon_window_2[1] - 2, image_info.latlon_window_1[0] + 2, image_info.latlon_window_2[1] + 2), fill=blue)
        draw.ellipse((image_info.latlon_window_2[0] - 2, image_info.latlon_window_1[1] - 2, image_info.latlon_window_2[0] + 2, image_info.latlon_window_1[1] + 2), fill=blue)

        stitched.show()
        """

        # Draw waypoints/lines:
        if polyline:
            self._draw_line(stitched, image_info, polyline, width=polyline_width, color=polyline_color)

        # Crop:
        cropped = self._crop(stitched, image_info);

        attribution = attribution if attribution != None else '(c) OSM contributors'
        self._draw_attribution(cropped, attribution, width, height)

        return cropped

    def _draw_attribution(self, image, attribution, width, height):
        font = mod_imagefont.load_default()
        label_width, label_height = font.getsize(attribution)
        draw = mod_imagedraw.Draw(image) 
        color = (255, 160, 0)
        draw.text((width - label_width, height - label_height), attribution, color, font)

    def _draw_line(self, stitched, image_info, polyline, width=None, color=None):
        width = width or 2
        color = color or (255, 0, 0)
        draw = mod_imagedraw.Draw(stitched) 
        for point_no in range(1, len(polyline)):
            point_1 = polyline[point_no - 1]
            point_2 = polyline[point_no]
            x1, y1 = self._get_position_on_stitched_image(image_info.tile_1, image_info.tile_2, point_1.latitude, point_1.longitude)
            x2, y2 = self._get_position_on_stitched_image(image_info.tile_1, image_info.tile_2, point_2.latitude, point_2.longitude)
            draw.line((x1, y1, x2, y2), fill=color, width=width)

    def _crop(self, stitched, image_info):
        return stitched.crop((int(image_info.widthheight_window_1[0]), int(image_info.widthheight_window_1[1]), \
                              int(image_info.widthheight_window_2[0]), int(image_info.widthheight_window_2[1])))

    def _stitch_tiles(self, tile_1, tile_2, tile_size):
        assert tile_1.zoom == tile_2.zoom
        zoom = tile_1.zoom
        x_range = range(min(tile_1.x, tile_2.x), max(tile_1.x, tile_2.x) + 1)
        y_range = range(min(tile_1.y, tile_2.y), max(tile_1.y, tile_2.y) + 1)

        horizontal_tiles = abs(tile_1.x - tile_2.x) + 1
        vertical_tiles = abs(tile_1.y - tile_2.y) + 1

        result = mod_image.new('RGB', (horizontal_tiles * tile_size, vertical_tiles * tile_size))

        for x in x_range:
            for y in y_range:
                tile = TileInfo(x, y, zoom)
                tile_url = tile.get_tile_url()
                mod_logging.debug('Downloading %s' % tile_url)
                req_result = mod_requests.get(tile_url)
                if not req_result.ok:
                    raise Exception('Error retrieving %s' % tile_url)
                """
                f = open(tile_url.replace('http://', '').replace('/', '_'), 'w')
                f.write(req_result.content)
                """
                tile_image = mod_image.open(mod_stringio.StringIO(req_result.content))
                result.paste(tile_image, (tile_size * (x - x_range[0]), tile_size * (y - y_range[0])))
                #print 'ok'

        return result
