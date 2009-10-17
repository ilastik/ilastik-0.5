from core import dataMgr
import cPickle as pickle

class Project(object):
    def __init__(self, name, labeler, description, dataMgr):
        self.name = name
        self.labeler = labeler
        self.description = description
        self.dataMgr = dataMgr
        self.labelNames = []
        self.labelColors = {}
    
    def saveToDisk(self, fileName):
        fileHandle = open(fileName,'wb')
        pickle.dump(self, fileHandle, True)
        fileHandle.close()
        print "Project %s saved to %s " % (self.name, fileName)
    
    @staticmethod
    def loadFromDisk(fileName):
        fileHandle = open(fileName,'rb')
        p = pickle.load(fileHandle)
        fileHandle.close()
        print "Project %s loaded from %s " % (p.name, fileName)
        return p
            
#    def setDataMgr(self, dataList):
#        self.dataMgr = dataMagr.dataMagr(dataList)
    