from ilastik.core.baseModuleMgr import BaseModuleDataItemMgr, BaseModuleMgr


#*******************************************************************************
# I n t e r a c t i v e C o n s o l e I t e m M o d u l e M g r                *
#*******************************************************************************

class InteractiveConsoleItemModuleMgr(BaseModuleDataItemMgr):
    name = "Interactive_Console"
    
    def __init__(self, dataItemImage):
        BaseModuleDataItemMgr.__init__(self, dataItemImage)
        self.dataItemImage = dataItemImage
        
    def serialize(self, h5g, destbegin = (0,0,0), destend = (0,0,0), srcbegin = (0,0,0), srcend = (0,0,0), destshape = (0,0,0) ):
        pass
    
    def deserialize(self, h5g, offsets, shape):
        pass
    

#*******************************************************************************
# I n t e r a c t i v e C o n s o l e M o d u l e M g r                        *
#*******************************************************************************

class InteractiveConsoleModuleMgr(BaseModuleMgr):
    name = "Interactive_Console"
        
    def __init__(self, dataMgr):
        BaseModuleMgr.__init__(self, dataMgr)
        self.dataMgr = dataMgr
        
        for i, im in enumerate(self.dataMgr):
            self.onNewImage(im)
            
    def onNewImage(self, dataItemImage):
        pass
    
    def onDeleteImage(self, dataItemImage):
        pass
    
    def serialize(self, h5g):
        pass
    
    def deserialize(self, h5g):
        pass    