from ilastik.core.baseModuleMgr import BaseModuleDataItemMgr, BaseModuleMgr
from ilastik.core.overlayMgr import OverlayItem
from ilastik.core.volume import DataAccessor
import numpy
import vigra

#*******************************************************************************
# A u t o m a t i c S e g m e n t a t i o n I t e m M o d u l e M g r          *
#*******************************************************************************

class AutomaticSegmentationItemModuleMgr(BaseModuleDataItemMgr):
    name = "Automatic_Segmentation"
    
    def __init__(self, dataItemImage):
        BaseModuleDataItemMgr.__init__(self, dataItemImage)
        self.dataItemImage = dataItemImage
        
    def serialize(self, h5g, destbegin = (0,0,0), destend = (0,0,0), srcbegin = (0,0,0), srcend = (0,0,0), destshape = (0,0,0) ):
        pass
    
    def deserialize(self, h5g, offsets, shape):
        pass
    

#*******************************************************************************
# A u t o m a t i c S e g m e n t a t i o n M o d u l e M g r                  *
#*******************************************************************************

class AutomaticSegmentationModuleMgr(BaseModuleMgr):
    name = "Automatic_Segmentation"
        
    def __init__(self, dataMgr):
        BaseModuleMgr.__init__(self, dataMgr)
        self.dataMgr = dataMgr
        
    def invertPotential(self, weights):
        return (255 - weights[:,:,:])    
        
    def normalizePotential(self, weights):
        #TODO: this , until now, only supports gray scale and 2D!
        min = numpy.min(weights)
        max = numpy.max(weights)
        weights = (weights - min)*(255.0 / (max - min))

        data = numpy.ndarray(weights.shape, 'float32')
        data[:] = weights[:]
        return data     
    
    def computeResults(self, input):
        self.res = numpy.ndarray((1,) + input.shape + (1,), 'int32')
        if input.shape[0] > 1:
            borders = input.view(vigra.ScalarVolume)
            self.res[0,:,:,:,0] = vigra.analysis.watersheds(borders, neighborhood = 6)[0]
        else:
            borders = input[0,:,:].view(vigra.ScalarImage)
            self.res[0,0,:,:,0] = vigra.analysis.watersheds(borders, 4)[0]
    
    def finalizeResults(self):
        colortable = OverlayItem.createDefaultColorTable('RGB', 256)

        #create Overlay for segmentation:
        if self.dataMgr[self.dataMgr._activeImageNumber].overlayMgr["Auto Segmentation/Segmentation"] is None:
            ov = OverlayItem(self.res, color = 0, alpha = 1.0, colorTable = colortable, autoAdd = True, autoVisible = True)
            self.dataMgr[self.dataMgr._activeImageNumber].overlayMgr["Auto Segmentation/Segmentation"] = ov
        else:
            self.dataMgr[self.dataMgr._activeImageNumber].overlayMgr["Auto Segmentation/Segmentation"]._data = DataAccessor(self.res)
        