from PyQt4 import QtCore
import sys
from ilastik.core.projectClass import Project
from ilastik.core.testThread import TestThread
from ilastik.modules.unsupervised_decomposition.core.unsupervisedMgr import UnsupervisedDecompositionModuleMgr
from ilastik.modules.unsupervised_decomposition.core.algorithms.unsupervisedDecompositionPLSA import UnsupervisedDecompositionPLSA
from ilastik.modules.unsupervised_decomposition.core.algorithms.unsupervisedDecompositionPCA import UnsupervisedDecompositionPCA
import unittest
from ilastik.core import jobMachine
from ilastik import __path__ as ilastikpath

class TestWholeModuleDefaultDecomposer(unittest.TestCase): # use default decomposer
     
    def setUp(self):
        #print "setUp"
        self.app = QtCore.QCoreApplication(sys.argv) # we need a QCoreApplication to run, otherwise the thread just gets killed
        self.testdir = ilastikpath[0] + "/testdata/unsupervised_decomposition/"
        print self.testdir
    
    def test_WholeModule(self):
        t = QtCore.QTimer()
        t.setSingleShot(True)
        t.setInterval(0)
        self.app.connect(t, QtCore.SIGNAL('timeout()'), self.mainFunction)        
        t.start()
        self.app.exec_()
        
    def mainFunction(self):
        # create project
        self.project = Project('Project Name', 'Labeler', 'Description')
        self.dataMgr = self.project.dataMgr
    
        # create file list and load data
        path = str(self.testdir + "sims_aligned_s7_32.h5")    
        fileList = []
        fileList.append(path)
        self.project.addFile(fileList)
        
        # create unsupervised manager
        self.unsupervisedMgr = UnsupervisedDecompositionModuleMgr(self.dataMgr)
    
        # setup inputs, compute results
        inputOverlays = []
        inputOverlays.append(self.dataMgr[self.dataMgr._activeImageNumber].overlayMgr["Raw Data"])
        
        # use default decomposer
        unsupervisedMethod = self.dataMgr.module["Unsupervised_Decomposition"].unsupervisedMethod
        
        # overlay lists and filenames
        listOfResultOverlays = []
        listOfFilenames = []
        for i in range(unsupervisedMethod.numComponents):
            listOfResultOverlays.append(str("Unsupervised/" + unsupervisedMethod.shortname + " component %d" % (i+1)))
            filename = str(self.testdir + "unsupervised_" + unsupervisedMethod.shortname + "_component_%d.h5" % (i+1))
            print filename
            listOfFilenames.append(filename)
        
        self.numOverlaysBefore = len(self.dataMgr[self.dataMgr._activeImageNumber].overlayMgr.keys())
        
        self.testThread = TestThread(self.unsupervisedMgr, listOfResultOverlays, listOfFilenames)
        QtCore.QObject.connect(self.testThread, QtCore.SIGNAL('done()'), self.finalizeTest)
        self.testThread.start(inputOverlays)

    def finalizeTest(self):
        # results comparison
        #print self.testThread.myTestThread.isFinished()
        self.assertEqual(self.testThread.passedTest, True)
        
        # other conditions
        # exactly 3 computed overlays + 3 ground truth overlays were added
        self.numOverlaysAfter = len(self.dataMgr[self.dataMgr._activeImageNumber].overlayMgr.keys())
        self.assertEqual(self.numOverlaysAfter - self.numOverlaysBefore, 6)
                
        self.app.quit()
        
class TestWholeModulePCADecomposer(unittest.TestCase): # use PCA decomposer with 3 components
     
    def setUp(self):
        #print "setUp"
        self.app = QtCore.QCoreApplication(sys.argv) # we need a QCoreApplication to run, otherwise the thread just gets killed
        self.testdir = ilastikpath[0] + "/testdata/unsupervised_decomposition/"
    
    def test_WholeModule(self):
        t = QtCore.QTimer()
        t.setSingleShot(True)
        t.setInterval(0)
        self.app.connect(t, QtCore.SIGNAL('timeout()'), self.mainFunction)        
        t.start()
        self.app.exec_()
        
    def mainFunction(self):
        # create project
        self.project = Project('Project Name', 'Labeler', 'Description')
        self.dataMgr = self.project.dataMgr
    
        # create file list and load data
        path = str(self.testdir + "sims_aligned_s7_32.h5")    
        fileList = []
        fileList.append(path)
        self.project.addFile(fileList)
        
        # create unsupervised manager
        self.unsupervisedMgr = UnsupervisedDecompositionModuleMgr(self.dataMgr)
    
        # setup inputs, compute results
        inputOverlays = []
        inputOverlays.append(self.dataMgr[self.dataMgr._activeImageNumber].overlayMgr["Raw Data"])
        
        # use PCA decomposer
        self.dataMgr.module["Unsupervised_Decomposition"].unsupervisedMethod = UnsupervisedDecompositionPCA
        self.dataMgr.module["Unsupervised_Decomposition"].unsupervisedMethod.setNumberOfComponents(3)
        
        # overlay lists and filenames
        listOfResultOverlays = []
        listOfFilenames = []
        for i in range(3):
            listOfResultOverlays.append("Unsupervised/PCA component %d" % (i+1))
            listOfFilenames.append(str(self.testdir + "unsupervised_PCA_component_%d.h5" % (i+1)))
                  
        self.numOverlaysBefore = len(self.dataMgr[self.dataMgr._activeImageNumber].overlayMgr.keys())
        
        self.testThread = TestThread(self.unsupervisedMgr, listOfResultOverlays, listOfFilenames)
        QtCore.QObject.connect(self.testThread, QtCore.SIGNAL('done()'), self.finalizeTest)
        self.testThread.start(inputOverlays)

    def finalizeTest(self):
        # results comparison
        #print self.testThread.myTestThread.isFinished()
        self.assertEqual(self.testThread.passedTest, True)
        
        # other conditions
        # exactly 3 computed overlays + 3 ground truth overlays were added
        self.numOverlaysAfter = len(self.dataMgr[self.dataMgr._activeImageNumber].overlayMgr.keys())
        self.assertEqual(self.numOverlaysAfter - self.numOverlaysBefore, 6)
                
        self.app.quit()
        
class TestWholeModulePLSADecomposer(unittest.TestCase): # pLSA with 5 components
     
    def setUp(self):
        #print "setUp"
        self.app = QtCore.QCoreApplication(sys.argv) 
        self.testdir = ilastikpath[0] + "/testdata/unsupervised_decomposition/"
    
    def test_WholeModule(self):
        t = QtCore.QTimer()
        t.setSingleShot(True)
        t.setInterval(0)
        self.app.connect(t, QtCore.SIGNAL('timeout()'), self.mainFunction)        
        t.start()
        self.app.exec_()
        
    def mainFunction(self):
        # create project
        self.project = Project('Project Name', 'Labeler', 'Description')
        self.dataMgr = self.project.dataMgr
    
        # create file list and load data
        path = str(self.testdir + "sims_aligned_s7_32.h5")    
        fileList = []
        fileList.append(path)
        self.project.addFile(fileList)
        
        # create unsupervised manager
        self.unsupervisedMgr = UnsupervisedDecompositionModuleMgr(self.dataMgr)
        
        # setup decomposition algorithm
        self.dataMgr.module["Unsupervised_Decomposition"].unsupervisedMethod = UnsupervisedDecompositionPLSA
        self.dataMgr.module["Unsupervised_Decomposition"].unsupervisedMethod.setNumberOfComponents(5)
        self.dataMgr.module["Unsupervised_Decomposition"].unsupervisedMethod.setRandomSeed()
    
        # setup inputs, compute results
        inputOverlays = []
        inputOverlays.append(self.dataMgr[self.dataMgr._activeImageNumber].overlayMgr["Raw Data"])
        
        # overlay lists and filenames
        listOfResultOverlays = []
        listOfFilenames = []
        for i in range(5):
            listOfResultOverlays.append("Unsupervised/pLSA component %d" % (i+1))
            listOfFilenames.append(str(self.testdir + "unsupervised_pLSA_component_%d.h5" % (i+1)))
        
        self.numOverlaysBefore = len(self.dataMgr[self.dataMgr._activeImageNumber].overlayMgr.keys())
        
        self.testThread = TestThread(self.unsupervisedMgr, listOfResultOverlays, listOfFilenames)
        QtCore.QObject.connect(self.testThread, QtCore.SIGNAL('done()'), self.finalizeTest)
        self.testThread.start(inputOverlays)

    def finalizeTest(self):
        # results comparison
        self.assertEqual(self.testThread.passedTest, True)
        
        # exactly 3 computed overlays + 3 ground truth overlays were added
        self.numOverlaysAfter = len(self.dataMgr[self.dataMgr._activeImageNumber].overlayMgr.keys())
        self.assertEqual(self.numOverlaysAfter - self.numOverlaysBefore, 10)
                
        self.app.quit()

# very stupid indeed, but necessary: the inclusion of the jobMachine (potentially indirect) results in a global 
# thread being started. To terminate it, we have to call the respective jobMachine function. But: this has 
# to be done in a tearDown function and it must only been done once, i.e. by the last test. Tests are executed
# in alphabetical order by unittest (default).   
class zzzTestDummy(unittest.TestCase): 
     
    def test_dummy(self):
        pass
        
    def tearDown(self):
        jobMachine.GLOBAL_WM.stopWorkers()

if __name__ == "__main__":
    unittest.main()
    jobMachine.GLOBAL_WM.stopWorkers()


