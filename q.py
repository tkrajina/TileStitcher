import logging as mod_logging
import tilestitcher as mod_tilestitcher

mod_logging.basicConfig(level=mod_logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')

slipy_map_tilenames = mod_tilestitcher.SlippyMapTilenames()

#print slipy_map_tilenames.get_image((45.2775, 45.2785), (13.7261, 13.8261), 400, 400)
print slipy_map_tilenames.get_image((45.2775, 46.3785), (13.5261, 14.9271), 200, 200)
