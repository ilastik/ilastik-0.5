from PyQt4 import QtCore
import sys
from ilastik.core.projectClass import Project
from ilastik.core.testThread import TestThread
from ilastik.modules.unsupervised_decomposition.core.unsupervisedMgr import UnsupervisedDecompositionModuleMgr
import unittest
from ilastik.core import jobMachine

class Tests(unittest.TestCase):
     
    def setUp(self):
        self.app = QtCore.QCoreApplication(sys.argv)
        #print "setUp"
    
    def test_WholeModule(self):
        t = QtCore.QTimer()
        t.setSingleShot(True)
        t.setInterval(0)
        self.app.connect(t, QtCore.SIGNAL('timeout()'), self.WholeModule)        
        t.start()
        self.app.exec_()
        
    def tearDown(self):
        print "tearDown"
        jobMachine.GLOBAL_WM.stopWorkers()
        
    def WholeModule(self):
        print "WholeModule"
        
        # create project
        project = Project('Project Name', 'Labeler', 'Description')
        dataMgr = project.dataMgr
    
        # create file list and load data
        path = '../../../../testdata/sims_aligned_s7_32.h5'    
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
        listOfFilenames.append("../../../../testdata/unsupervised_PCA_component_1.h5")
        listOfFilenames.append("../../../../testdata/unsupervised_PCA_component_2.h5")
        listOfFilenames.append("../../../../testdata/unsupervised_PCA_component_3.h5")
        
        self.testThread = TestThread(unsupervisedMgr, listOfResultOverlays, listOfFilenames)
        QtCore.QObject.connect(self.testThread, QtCore.SIGNAL('done()'), self.collectOutcomes)
        self.testThread.start(inputOverlays)
        self.assertEqual(True, True)

    def collectOutcomes(self):
        #print "Test outcomes:"
        #print self.testThread.passedTest
        #print "Done."
        #print self.testThread.myTestThread.isFinished()
        self.assertEqual(self.testThread.passedTest, True)
        self.app.quit()

if __name__ == "__main__":
    unittest.main()



