import numpy
import overlayBase
import ilastik.core.overlayMgr as overlayMgr
from ilastik.core.volume import DataAccessor
from PyQt4 import QtGui

class NormalizeOverlay(overlayBase.OverlayBase, overlayMgr.OverlayItem):
    def __init__(self, data, nMin, nMax, autoAdd = True, autoVisible = True):
        overlayBase.OverlayBase.__init__(self)
        data = data._data._data.astype(numpy.float32) 
        data = numpy.clip(data, nMin, nMax)
        data = ((data - nMin) / (nMax-nMin)*255).astype(numpy.uint8)
        self.data = DataAccessor(data)
        overlayMgr.OverlayItem.__init__(self, self.data, color = QtGui.QColor(255, 255, 255), alpha = 1.0, autoAdd = autoAdd, autoVisible = autoVisible,  linkColorTable = True, autoAlphaChannel=False)
        
    def getColorTab(self):
        return None