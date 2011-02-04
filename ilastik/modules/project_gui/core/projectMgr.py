from ilastik.core.baseModuleMgr import BaseModuleDataItemMgr, BaseModuleMgr


class ProjectItemModuleMgr(BaseModuleDataItemMgr):
    name = "Project"
    
    def __init__(self, dataItemImage):
        BaseModuleDataItemMgr.__init__(self, dataItemImage)
        self.dataItemImage = dataItemImage
        
    def serialize(self, h5g, destbegin = (0,0,0), destend = (0,0,0), srcbegin = (0,0,0), srcend = (0,0,0), destshape = (0,0,0) ):
        pass
    
    def deserialize(self, h5g, offsets, shape):
        pass
    

class ProjectModuleMgr(BaseModuleMgr):
    name = "Project"
        
    def __init__(self, dataMgr):
        BaseModuleMgr.__init__(self, dataMgr)
        self.dataMgr = dataMgr

    def loadStack(self, fileList, options):
        print len(fileList)
        print len(fileList[0])
        

    def onNewImage(self, dataItemImage):
        pass
    
    def onDeleteImage(self, dataItemImage):
        pass
    
    def serialize(self, h5g):
        pass
    
    def deserialize(self, h5g):
        pass    