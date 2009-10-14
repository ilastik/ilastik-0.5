import numpy

try:
    from vigra import vigranumpycmodule as vm
except:
    try:
        import vigranumpycmodule as vm
    except:
        pass

class DataItemBase():
    def __init__(self, fileName):
        self.fileName = str(fileName)
        self.hasLabels = False
        self.isTraining = True
        self.isTesting = False
        self.groupMember = []
        self.projects = []
        
        self.data = None
        self.labels = []
        self.dataType = None
        self.dataDimensions = []
        self.thumbnail = None
        
    def loadData(self):
        self.data = "This is not an Image..."

class DataItemImage(DataItemBase):
    def __init__(self, fileName):
        DataItemBase.__init__(self, fileName) 
       
    def loadData(self):
        self.data = vm.readImage(self.fileName)
        
    def unLoadData(self):
        # TODO: delete permanently here for better garbage collection
        self.data = None
        
class DataMgr():
    def __init__(self, dataItems=[]):
        self.setDataList(dataItems)
        self.dataFeatures = []
        self.labels = [None] * len(dataItems)
        
    def setDataList(self, dataItems):
        self.dataItems = dataItems
        self.dataItemsLoaded = [False] * len(dataItems)
        
    def __getitem__(self, ind):
        if not self.dataItemsLoaded[ind]:
            self.dataItems[ind].loadData()
            self.dataItemsLoaded[ind] = True
        return self.dataItems[ind]
    
    def __len__(self):
        return len(self.dataItems)
        
        


        
