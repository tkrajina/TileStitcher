import tilestitcher as mod_tilestitcher

slipy_map_tilenames = mod_tilestitcher.SlippyMapTilenames()

#print slipy_map_tilenames.get_image((0., 1.), (0., 1.), 300, 300)
#print slipy_map_tilenames.get_image((45.2775, 45.2785), (13.7261, 13.8261), 200)
print slipy_map_tilenames.get_image((45.2775, 45.3785), (13.7261, 13.7271), 100, 300)
