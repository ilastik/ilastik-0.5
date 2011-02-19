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

class UnsupervisedDecompositionTestProject(object):
    # this class is used to set up a default project which is then used for testing functionality, 
    # hopefully, this will reduced code redundancy
    def __init__(self, image_filename, unsupervisedMethod = None, numComponents = None):
        
        self.image_filename = image_filename
        
        self.testdir = ilastikpath[0] + "/testdata/unsupervised_decomposition/"
        
        # create project
        self.project = Project('Project Name', 'Labeler', 'Description')
        self.dataMgr = self.project.dataMgr
    
        # create file list and load data
        path = str(self.testdir + self.image_filename) # the image is not really used since we load the threshold overlay from a file, however, we need it to set the correct dimensions 
        fileList = []
        fileList.append(path)
        self.project.addFile(fileList)
        
        # create automatic segmentation manager
        self.unsupervisedMgr = UnsupervisedDecompositionModuleMgr(self.dataMgr)
    
        # setup inputs
        self.inputOverlays = []
        self.inputOverlays.append(self.dataMgr[self.dataMgr._activeImageNumber].overlayMgr["Raw Data"])
        
        # use default decomposer
        if unsupervisedMethod is None:
            self.unsupervisedMethod = self.dataMgr.module["Unsupervised_Decomposition"].unsupervisedMethod
        else:
            self.unsupervisedMethod = self.dataMgr.module["Unsupervised_Decomposition"].unsupervisedMethod = unsupervisedMethod
        if numComponents is not None:
            self.unsupervisedMethod.setNumberOfComponents(numComponents)    
            self.numIterations = numComponents
        else:
            self.numIterations = self.unsupervisedMethod.numComponents
        
        # overlay lists and filenames
        self.listOfResultOverlays = []
        self.listOfFilenames = []
        for i in range(self.numIterations):
            self.listOfResultOverlays.append(str("Unsupervised/" + self.unsupervisedMethod.shortname + " component %d" % (i+1)))
            filename = str(self.testdir + "unsupervised_" + self.unsupervisedMethod.shortname + "_component_%d.h5" % (i+1))
            print filename
            self.listOfFilenames.append(filename)        


class TestWholeModuleDefaultDecomposer(unittest.TestCase): # use default decomposer

    def setUp(self):
        #print "setUp"
        self.app = QtCore.QCoreApplication(sys.argv) # we need a QCoreApplication to run, otherwise the thread just gets killed
        self.testProject = UnsupervisedDecompositionTestProject("sims_aligned_s7_32.h5")
    
    def test_WholeModule(self):
        t = QtCore.QTimer()
        t.setSingleShot(True)
        t.setInterval(0)
        self.app.connect(t, QtCore.SIGNAL('timeout()'), self.mainFunction)        
        t.start()
        self.app.exec_()
        
    def mainFunction(self):
        self.testThread = TestThread(self.testProject.unsupervisedMgr, self.testProject.listOfResultOverlays, self.testProject.listOfFilenames)
        QtCore.QObject.connect(self.testThread, QtCore.SIGNAL('done()'), self.finalizeTest)
        self.testThread.start(self.testProject.inputOverlays)        

        self.numOverlaysBefore = len(self.testProject.dataMgr[self.testProject.dataMgr._activeImageNumber].overlayMgr.keys())

    def finalizeTest(self):
        # results comparison
        self.assertEqual(self.testThread.passedTest, True)
                
        self.app.quit()
        
        
class TestWholeModulePCADecomposer(unittest.TestCase): # use PCA decomposer with 3 components
     
    def setUp(self):
        #print "setUp"
        self.app = QtCore.QCoreApplication(sys.argv) # we need a QCoreApplication to run, otherwise the thread just gets killed
        self.numComponents = 3
        self.testProject = UnsupervisedDecompositionTestProject("sims_aligned_s7_32.h5", UnsupervisedDecompositionPCA, self.numComponents)
    
    def test_WholeModule(self):
        t = QtCore.QTimer()
        t.setSingleShot(True)
        t.setInterval(0)
        self.app.connect(t, QtCore.SIGNAL('timeout()'), self.mainFunction)        
        t.start()
        self.app.exec_()
        
    def mainFunction(self):
        self.testThread = TestThread(self.testProject.unsupervisedMgr, self.testProject.listOfResultOverlays, self.testProject.listOfFilenames)
        QtCore.QObject.connect(self.testThread, QtCore.SIGNAL('done()'), self.finalizeTest)
        self.testThread.start(self.testProject.inputOverlays)        

        self.numOverlaysBefore = len(self.testProject.dataMgr[self.testProject.dataMgr._activeImageNumber].overlayMgr.keys())

    def finalizeTest(self):
        # results comparison
        self.assertEqual(self.testThread.passedTest, True)
        
        # other conditions
        # exactly self.numComponents computed overlays + self.numComponents ground truth overlays were added
        self.numOverlaysAfter = len(self.testProject.dataMgr[self.testProject.dataMgr._activeImageNumber].overlayMgr.keys())
        self.assertEqual(self.numOverlaysAfter - self.numOverlaysBefore, self.numComponents*2)

        self.app.quit()
        
class TestWholeModulePLSADecomposer(unittest.TestCase): # pLSA with 5 components
     
    def setUp(self):
        #print "setUp"
        self.app = QtCore.QCoreApplication(sys.argv) 
        self.numComponents = 5
        self.testProject = UnsupervisedDecompositionTestProject("sims_aligned_s7_32.h5", UnsupervisedDecompositionPLSA, self.numComponents)
    
    def test_WholeModule(self):
        t = QtCore.QTimer()
        t.setSingleShot(True)
        t.setInterval(0)
        self.app.connect(t, QtCore.SIGNAL('timeout()'), self.mainFunction)        
        t.start()
        self.app.exec_()
        
    def mainFunction(self):
        # fix random seed
        from ilastik.core.randomSeed import RandomSeed
        RandomSeed.setRandomSeed(42)
        
        self.testThread = TestThread(self.testProject.unsupervisedMgr, self.testProject.listOfResultOverlays, self.testProject.listOfFilenames)
        QtCore.QObject.connect(self.testThread, QtCore.SIGNAL('done()'), self.finalizeTest)
        self.testThread.start(self.testProject.inputOverlays)        

        self.numOverlaysBefore = len(self.testProject.dataMgr[self.testProject.dataMgr._activeImageNumber].overlayMgr.keys())

    def finalizeTest(self):
        # results comparison
        self.assertEqual(self.testThread.passedTest, True)
        
        # exactly self.numComponents computed overlays + self.numComponents ground truth overlays were added
        self.numOverlaysAfter = len(self.testProject.dataMgr[self.testProject.dataMgr._activeImageNumber].overlayMgr.keys())
        self.assertEqual(self.numOverlaysAfter - self.numOverlaysBefore, self.numComponents*2)
                
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


