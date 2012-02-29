import numpy
import overlayBase
import ilastik.core.overlayMgr as overlayMgr
from ilastik.core.volume import DataAccessor
from PyQt4 import QtGui

class NormalizeOverlay(overlayBase.OverlayBase, overlayMgr.OverlayItem):
    def __init__(self, overlay, nMin, nMax, autoAdd = True, autoVisible = True):
        overlayBase.OverlayBase.__init__(self)
        self.overlay = overlay
        self.nMin = nMin
        self.nMax = nMax 
        
    def normalize(self):
        orig_data = self.overlay._data._data.astype(numpy.float32) 
        norm_data = numpy.clip(orig_data, self.nMin, self.nMax)
        norm_data = ((norm_data - self.nMin) / (self.nMax-self.nMin)*255).astype(numpy.uint8)
        overlayMgr.OverlayItem.__init__(self, DataAccessor(norm_data), color = QtGui.QColor(255, 255, 255), alpha = 1.0, autoAdd = True, autoVisible = True,  linkColorTable = True, autoAlphaChannel=False)
        
    def getColorTab(self):
        return None