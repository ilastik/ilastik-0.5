from PyQt4 import QtCore
import sys
from ilastik.core.projectClass import Project
from ilastik.core.testThread import TestThread
from ilastik.modules.unsupervised_decomposition.core.unsupervisedMgr import UnsupervisedDecompositionModuleMgr

class Tests():
    
    def __init__(self, parent = None):
        self.parent = parent
    
    def testWholeModule(self):
        # create project
        project = Project('Project Name', 'Labeler', 'Description')
        dataMgr = project.dataMgr
    
        # create file list and load data
        path = '../../../../sims_aligned_s7_32.h5'    
        fileList = []
        fileList.append(path)
        project.addFile(fileList)
        
        # create unsupervised manager
        unsupervisedMgr = UnsupervisedDecompositionModuleMgr(dataMgr)
    
        # setup inputs, compute results
        inputOverlays = []
        inputOverlays.append(dataMgr[dataMgr._activeImageNumber].overlayMgr["Raw Data"])
        
        # overlay lists and filenames
        listOfResultOverlays = []
        listOfResultOverlays.append("Unsupervised/PCA component 1")
        listOfResultOverlays.append("Unsupervised/PCA component 2")
        listOfResultOverlays.append("Unsupervised/PCA component 3")
        listOfFilenames = []
        listOfFilenames.append("unsupervised_PCA_component_1.h5")
        listOfFilenames.append("unsupervised_PCA_component_2.h5")
        listOfFilenames.append("unsupervised_PCA_component_3.h5")
        
        self.testThread = TestThread(self.parent, unsupervisedMgr, listOfResultOverlays, listOfFilenames)
        self.testThread.start(inputOverlays)
        QtCore.QObject.connect(self.testThread, QtCore.SIGNAL('done()'), self.collectOutcomes)
        

    def collectOutcomes(self):
        print "Test outcomes:"
        print self.testThread.passedTest
        print "Done."

if __name__ == "__main__":
    app = QtCore.QCoreApplication(sys.argv)
        
    myTests = Tests(app)
    myTests.testWholeModule()

    app.exec_()
    sys.exit()

