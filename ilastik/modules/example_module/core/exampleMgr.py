from ilastik.core.baseModuleMgr import BaseModuleDataItemMgr, BaseModuleMgr


#*******************************************************************************
# E x a m p l e I t e m M o d u l e M g r                                      *
#*******************************************************************************

class ExampleItemModuleMgr(BaseModuleDataItemMgr):
    name = "Example"
    
    """
    an instance of this class is created on any newly created DataItemImage
    it is available in a dataItemImage instance variable called
    after the name property of this class
    
    e.g. in this case: dataItemImage.Example
    
    you can save any DataItemImage specific private state
    in this class
    
    the __init__ function should not depend on the underlying dataItemImage being
    already loaded and fully available (e.g. don't access self.dataItemImage.shape for example)
    
    the underlying dataItemImage is only available after
    the onNewImage function of the BaseModuleMgr has been called !
    """
    
    def __init__(self, dataItemImage):
        BaseModuleDataItemMgr.__init__(self, dataItemImage)
        self.dataItemImage = dataItemImage
        
    def serialize(self, h5g, destbegin = (0,0,0), destend = (0,0,0), srcbegin = (0,0,0), srcend = (0,0,0), destshape = (0,0,0) ):
        """
        this function gets called whenever
        a DataItem is saved.
        
        the h5g parameter contains a h5py group in which
        any private state can be saved
        
        Note: this function is called after the
        BaseModuleMgr serialize function
        """
        pass
    
    def deserialize(self, h5g, offsets, shape):
        """
        this function gets called whenever
        a DataItem is deserialized.
        
        the h5g parameter contains a h5py group from which
        any previously saved private state can be retrieved
        
        Note: this function is called after the
        BaseModuleMgr deserialize function
        """
        pass
    

#*******************************************************************************
# E x a m p l e M o d u l e M g r                                              *
#*******************************************************************************

class ExampleModuleMgr(BaseModuleMgr):
    name = "Example"
    
    """
    an instance of this class is created on any newly created DataMgr
    it is available in a DataMge instance variable called
    after the name property of this class
    
    e.g. in this case: dataMgr.Example
    
    you can save any DataMgr specific private state
    in this class, e.g. state that needs to be tracked accross 
    multiple dataItemImages
    
    an example would be classifier trainingData that inherently depends
    on the trainingData of all DataItemImages.
    you would want to track the combined training data in this classs
    """
        
    def __init__(self, dataMgr):
        BaseModuleMgr.__init__(self, dataMgr)
        self.dataMgr = dataMgr

    def onNewImage(self, dataItemImage):
        """
        this function gets called whenever
        a DataItemImage is added to a DataMgr
        
        you should set up any private context within your
        ExampleItemModuleMgr
        
        and apply any needed state changes within this ModuleMgr if it
        depends on the single DataItems
        """
        pass
    
    def onDeleteImage(self, dataItemImage):
        """
        this function gets called whenever
        a DataItemImage is removed from a DataMgr
        
        you should free up any private context within your
        ExampleItemModuleMgr
        
        and apply any needed state changes within this ModuleMgr if it
        depends on the single DataItems
        """
        pass
    
    def serialize(self, h5g):
        """
        this function gets called whenever
        a project is saved.
        
        the h5g parameter contains a h5py group in which
        any private state can be saved
        
        Note: this function is called before the individual
        BaseDataItemModuleMgr serialize function
        """
        pass
    
    def deserialize(self, h5g):
        """
        this function gets called whenever
        a project is loaded.
        
        the h5g parameter contains a h5py group from which
        any previously saved state can be retrieved

        Note: this function is called before the individual
        BaseDataItemModuleMgr deserialize function

        """
        pass    