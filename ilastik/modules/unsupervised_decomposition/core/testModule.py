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

from ilastik.core.testThread import setUp, tearDown

# make sure that we have a recent numpy installation, the SVD used for PCA decomposition seems to have changed, resulting in a test failure!
import numpy
numpyversion = numpy.__version__.split('.')
numpyTooOldMessage = str("Your current numpy version is too old. Is: " + numpy.__version__ + " Should Be: 1.4.0 or newer. Skipping some tests.")
numpyRecentEnough = False
if((int(numpyversion[0]) >= 1) & (int(numpyversion[1]) >= 4) & (int(numpyversion[2]) >= 0)):
    numpyRecentEnough = True

#*******************************************************************************
# U n s u p e r v i s e d D e c o m p o s i t i o n T e s t P r o j e c t      *
#*******************************************************************************

class UnsupervisedDecompositionTestProject(object):
    # this class is used to set up a default project which is then used for testing functionality, 
    # hopefully, this will reduced code redundancy
    def __init__(self, image_filename, unsupervisedMethod = None, numComponents = None):
        
        self.image_filename = image_filename
        
        self.tolerance = 0.01 # maximum derivation per pixel
        
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
            filename = str(self.testdir + "gt_" + self.unsupervisedMethod.shortname + "_result_component_%d.h5" % (i+1))
            print filename
            self.listOfFilenames.append(filename)        


#*******************************************************************************
# T e s t W h o l e M o d u l e D e f a u l t D e c o m p o s e r              *
#*******************************************************************************

class TestWholeModuleDefaultDecomposer(unittest.TestCase): # use default decomposer

    if not numpyRecentEnough:
        __test__ = False

    def setUp(self):
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
        self.testThread = TestThread(self.testProject.unsupervisedMgr, self.testProject.listOfResultOverlays, self.testProject.listOfFilenames, self.testProject.tolerance)
        QtCore.QObject.connect(self.testThread, QtCore.SIGNAL('done()'), self.finalizeTest)
        self.testThread.start(self.testProject.inputOverlays)        

        self.numOverlaysBefore = len(self.testProject.dataMgr[self.testProject.dataMgr._activeImageNumber].overlayMgr.keys())

    def finalizeTest(self):
        # results comparison
        self.assertEqual(self.testThread.passedTest, True)
                
        self.app.quit()
        
        
#*******************************************************************************
# T e s t W h o l e M o d u l e P C A D e c o m p o s e r                      *
#*******************************************************************************

class TestWholeModulePCADecomposer(unittest.TestCase): # use PCA decomposer with 3 components

    if not numpyRecentEnough:
        __test__ = False
     
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
        self.testThread = TestThread(self.testProject.unsupervisedMgr, self.testProject.listOfResultOverlays, self.testProject.listOfFilenames, self.testProject.tolerance)
        QtCore.QObject.connect(self.testThread, QtCore.SIGNAL('done()'), self.finalizeTest)
        self.testThread.start(self.testProject.inputOverlays)        

        self.numOverlaysBefore = len(self.testProject.dataMgr[self.testProject.dataMgr._activeImageNumber].overlayMgr.keys())

    def finalizeTest(self):
        '''for i in range(self.testProject.unsupervisedMethod.numComponents):
            print "*************************************"
            print self.testProject.listOfResultOverlays[i]
            obtained = self.testProject.dataMgr[self.testProject.dataMgr._activeImageNumber].overlayMgr[self.testProject.listOfResultOverlays[i]]
            from ilastik.core import dataImpex
            dataImpex.DataImpex.exportOverlay(str("c:/gt_PCA_result_component_%d" % (i+1)), "h5", obtained)'''
        
         # results comparison
        self.assertEqual(self.testThread.passedTest, True)
        
        # other conditions
        # exactly self.numComponents computed overlays + self.numComponents ground truth overlays were added
        self.numOverlaysAfter = len(self.testProject.dataMgr[self.testProject.dataMgr._activeImageNumber].overlayMgr.keys())
        self.assertEqual(self.numOverlaysAfter - self.numOverlaysBefore, self.numComponents*2)

        self.app.quit()
        
#*******************************************************************************
# T e s t W h o l e M o d u l e P L S A D e c o m p o s e r                    *
#*******************************************************************************

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
        
        self.testThread = TestThread(self.testProject.unsupervisedMgr, self.testProject.listOfResultOverlays, self.testProject.listOfFilenames, self.testProject.tolerance)
        QtCore.QObject.connect(self.testThread, QtCore.SIGNAL('done()'), self.finalizeTest)
        self.testThread.start(self.testProject.inputOverlays)        

        self.numOverlaysBefore = len(self.testProject.dataMgr[self.testProject.dataMgr._activeImageNumber].overlayMgr.keys())

    def finalizeTest(self):
        '''for i in range(self.testProject.unsupervisedMethod.numComponents):
            obtained = self.testProject.dataMgr[self.testProject.dataMgr._activeImageNumber].overlayMgr[self.testProject.listOfResultOverlays[i]]
            from ilastik.core import dataImpex
            dataImpex.DataImpex.exportOverlay(str("c:/gt_pLSA_result_component_%d" % (i+1)), "h5", obtained)'''
        
        # results comparison
        self.assertEqual(self.testThread.passedTest, True)
        
        # exactly self.numComponents computed overlays + self.numComponents ground truth overlays were added
        self.numOverlaysAfter = len(self.testProject.dataMgr[self.testProject.dataMgr._activeImageNumber].overlayMgr.keys())
        self.assertEqual(self.numOverlaysAfter - self.numOverlaysBefore, self.numComponents*2)
                
        self.app.quit()
        

#*******************************************************************************
# T e s t E t c                                                                *
#*******************************************************************************

class TestEtc(unittest.TestCase): # test additional functionality
    
    def test_Etc(self):
        # check that wrong numbers of components are reset to a valid value in {1, ..., numComponents}
        numChannels = 10
        decomposer = UnsupervisedDecompositionPCA()
        components = decomposer.checkNumComponents(numChannels, 100)
        assert((components <= numChannels) & (components >= 1))
        components = decomposer.checkNumComponents(numChannels, 0)
        print components
        assert((components <= numChannels) & (components >= 1))


#*******************************************************************************
# i f   _ _ n a m e _ _   = =   " _ _ m a i n _ _ "                            *
#*******************************************************************************

if __name__ == "__main__":
    unittest.main()


