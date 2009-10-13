from core import dataMgr

class Project():
    def __init__(self, name, labeler, description, dataMgr):
        self.name = name
        self.labeler = labeler
        self.description = description
        self.dataMgr = dataMgr
        
#    def setDataMgr(self, dataList):
#        self.dataMgr = dataMagr.dataMagr(dataList)
    