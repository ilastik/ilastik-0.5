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

class BaseModuleDataItemMgr(PropertyMgr):
    """
    abstract base class for modules controlling a DataItem
    """
    def __init__(self, parent):
        PropertyMgr.__init__(self, parent)
    
    def onModuleStart(self):
        pass
    
    def onModuleStop(self):
        pass
    
    def serialize(self, h5g):
        pass
    
    def deserialize(self, h5g):
        pass



class BaseModuleMgr(PropertyMgr):
    """
    abstract base class for modules
    """
    name = "BaseModuleMgr"
    
    def __init__(self, parent):
        PropertyMgr.__init__(self, parent)
    
    def onModuleStart(self):
        pass
    
    def onModuleStop(self):
        pass
    
    def onNewImage(self, dataItemImage):
        pass
    
    def onDeleteImage(self, dataItemImage):
        pass
    