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
        self.trainingMatrix = None
        self.trainingLabels = None
        self.trainingFeatureNames = None
    
    def saveToDisk(self, fileName):
        """ Save the whole project includeing data, feautues, labels and settings to 
        and hdf5 file with ending ilp """
        
        # pickle.dump(self, fileHandle, True)
        
        # get project settings
        
        # get number of images
        
        # get data
        
        # get labels
        
        # get features
        
        
        fileHandle = open(fileName,'wb')
        # Save to hdf5 file
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
    