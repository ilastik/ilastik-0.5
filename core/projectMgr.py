class Project():
    def __init__(self, name, labeler, description, dataList):
        self.name = name
        self.labeler = labeler
        self.description = description
        self.dataList = dataList
        
    def setDataList(self, dataList):
        self.dataList = dataList
    