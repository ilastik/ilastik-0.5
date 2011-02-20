from ilastik.core.overlayMgr import OverlayReferenceMgr

from PyQt4.QtCore import QObject

#*******************************************************************************
# P r o p e r t y M g r                                                        *
#*******************************************************************************

class PropertyMgr(object):
    """
    Holds a bag of Properties that can be serialized and deserialized
    new properties are also added to the parents regular attributes
    for easier access
    """
    def __init__(self, parent):
        self._dict = {}
        self._parent = parent
        
    def serialize(self, h5g, name):
        for v in self.values():
            if hasattr(v, "serialize"):
                v.serialize(h5g)
    
    def deserialize(self, h5g, name):
        pass

    def keys(self):
        return self._dict.keys()
    
    def values(self):
        return self._dict.values()

    def __setitem__(self,  key,  value):
        self._dict[key] = value
        setattr(self._parent, key, value)
    
    def __getitem__(self, key):
        try:
            answer =  self._dict[key]
        except:
            answer = None
        return answer

#*******************************************************************************
# B a s e M o d u l e D a t a I t e m M g r                                    *
#*******************************************************************************

class BaseModuleDataItemMgr(PropertyMgr, QObject):
    """
    abstract base class for modules controlling a DataItem
    """
    name =  "BaseModuleDataItemMgr"
    
    def __init__(self, dataItemImage):
        self.dataItem = dataItemImage        
        PropertyMgr.__init__(self, dataItemImage)
        QObject.__init__(self)
        self.overlayReferences = OverlayReferenceMgr()
        self.globalMgr = None
        
    def onModuleStart(self):
        pass
    
    def onModuleStop(self):
        pass
    
    def getOverlayRefs(self):
        return self.overlayReferences
    
    def insertOverlayRef(self, position, ov):
        self.overlayReferences.insert(position, ov)

    def addOverlayRef(self, ov):
        if len(self.overlayReferences) >= 1:
            self.overlayReferences.insert(1, ov)
        else:
            self.overlayReferences.insert(0, ov)
            
    def serialize(self, h5g, destbegin = (0,0,0), destend = (0,0,0), srcbegin = (0,0,0), srcend = (0,0,0), destshape = (0,0,0) ):
        pass
    
    def deserialize(self, h5g, offsets, shape):
        pass



#*******************************************************************************
# B a s e M o d u l e M g r                                                    *
#*******************************************************************************

class BaseModuleMgr(PropertyMgr, QObject):
    """
    abstract base class for modules
    """
    name = "BaseModuleMgr"
    
    def __init__(self, dataMgr):
        PropertyMgr.__init__(self, dataMgr)
        QObject.__init__(self)
    
    def onModuleStart(self):
        pass
    
    def onModuleStop(self):
        pass
    
    def onNewImage(self, dataItemImage):
        pass
    
    def onDeleteImage(self, dataItemImage):
        pass
    
    def computeResults(self, input):
        pass
    
    def finalizeResults(self):
        pass
    
    def serialize(self, h5g):
        pass
    
    def deserialize(self, h5g):
        pass    
    