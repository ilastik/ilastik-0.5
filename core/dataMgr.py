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
        self.fileName = fileName
        self.hasLabels = False
        self.isTraining = True
        self.isTesting = False
        self.groupMember = []
        self.project = []
        
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