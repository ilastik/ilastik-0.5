from ilastik.core.baseModuleMgr import BaseModuleDataItemMgr, BaseModuleMgr


class HelpItemModuleMgr(BaseModuleDataItemMgr):
    name = "Help"
    
    def __init__(self, dataItemImage):
        BaseModuleDataItemMgr.__init__(self, dataItemImage)
        self.dataItemImage = dataItemImage
        
    def serialize(self, h5g, destbegin = (0,0,0), destend = (0,0,0), srcbegin = (0,0,0), srcend = (0,0,0), destshape = (0,0,0) ):
        pass
    
    def deserialize(self, h5g, offsets, shape):
        pass
    

class HelpModuleMgr(BaseModuleMgr):
    name = "Help"
        
    def __init__(self, dataMgr):
        BaseModuleMgr.__init__(self, dataMgr)
        self.dataMgr = dataMgr

    def onNewImage(self, dataItemImage):
        pass
    
    def onDeleteImage(self, dataItemImage):
        pass
    
    def serialize(self, h5g):
        pass
    
    def deserialize(self, h5g):
        pass    