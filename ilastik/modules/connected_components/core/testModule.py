from PyQt4 import QtCore
import sys
from ilastik.core.projectClass import Project
from ilastik.modules.connected_components.core.connectedComponentsMgr import ConnectedComponentsModuleMgr
import unittest
from ilastik.core.testThread import TestThread
from ilastik.core import dataImpex
from ilastik.core import jobMachine
from ilastik import __path__ as ilastikpath

class TestWholeModule(unittest.TestCase):
     
    def setUp(self):
        #print "setUp"
        self.app = QtCore.QCoreApplication(sys.argv) # we need a QCoreApplication to run, otherwise the thread just gets killed
        self.testdir = ilastikpath[0] + "/testdata/connected_components/"
    
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
        path = str(self.testdir + "test_image.png") # the image is not really used since we load the threshold overlay from a file, however, we need it to set the correct dimensions 
        fileList = []
        fileList.append(path)
        self.project.addFile(fileList)
        
        # create automatic segmentation manager
        self.connectedComponentsMgr = ConnectedComponentsModuleMgr(self.dataMgr)
    
        # setup inputs, compute results
        inputOverlays = []
        inputOverlays.append(self.dataMgr[self.dataMgr._activeImageNumber].overlayMgr["Raw Data"])
        
        # load precalculated threshold overlay from file
        dataImpex.DataImpex.importOverlay(self.dataMgr[self.dataMgr._activeImageNumber], str(self.testdir + "cc_threshold_overlay.h5"), "")
        
        # overlay lists and filenames
        listOfResultOverlays = []
        listOfFilenames = []
        listOfResultOverlays.append("Connected Components/CC Results")
        listOfFilenames.append(self.testdir + "ground_truth_cc_without_background.h5")
        
        # calculate connected components results
        # ...import threshold overlay
        threshold_ov = self.dataMgr[self.dataMgr._activeImageNumber].overlayMgr["Custom Overlays/Threshold Overlay"]
        self.dataMgr[self.dataMgr._activeImageNumber].Connected_Components.setInputOverlay(threshold_ov)
        
        self.testThread = TestThread(self.connectedComponentsMgr, listOfResultOverlays, listOfFilenames)
        QtCore.QObject.connect(self.testThread, QtCore.SIGNAL('done()'), self.finalizeTest)
        self.testThread.start(None) # ...compute connected components without background

    def finalizeTest(self):
        # results comparison
        self.assertEqual(self.testThread.passedTest, True)
        self.app.quit()

class TestWholeModuleWrongImage(unittest.TestCase): # tests if wrong input leads to a test fail
     
    def setUp(self):
        #print "setUp"
        self.app = QtCore.QCoreApplication(sys.argv) # we need a QCoreApplication to run, otherwise the thread just gets killed
        self.testdir = ilastikpath[0] + "/testdata/connected_components/"
    
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
        path = str(self.testdir + "test_image_mirrored.png") # the image is not really used since we load the threshold overlay from a file, however, we need it to set the correct dimensions 
        fileList = []
        fileList.append(path)
        self.project.addFile(fileList)
        
        # create automatic segmentation manager
        self.connectedComponentsMgr = ConnectedComponentsModuleMgr(self.dataMgr)
    
        # setup inputs, compute results
        inputOverlays = []
        inputOverlays.append(self.dataMgr[self.dataMgr._activeImageNumber].overlayMgr["Raw Data"])
        
        # load precalculated threshold overlay from file
        dataImpex.DataImpex.importOverlay(self.dataMgr[self.dataMgr._activeImageNumber], str(self.testdir + "cc_threshold_overlay.h5"), "")
        
        # overlay lists and filenames
        listOfResultOverlays = []
        listOfFilenames = []
        listOfResultOverlays.append("Connected Components/CC Results")
        listOfFilenames.append(self.testdir + "ground_truth_cc_without_background.h5")
        
        # calculate connected components results
        # ...import threshold overlay
        threshold_ov = self.dataMgr[self.dataMgr._activeImageNumber].overlayMgr["Custom Overlays/Threshold Overlay"]
        # ...randomly exchange some pixels
        import numpy
        for i in range(10):
            threshold_ov._data._data[numpy.random.randint(threshold_ov._data._data.shape[0]), numpy.random.randint(threshold_ov._data._data.shape[1]), numpy.random.randint(threshold_ov._data._data.shape[2]), numpy.random.randint(threshold_ov._data._data.shape[3]), numpy.random.randint(threshold_ov._data._data.shape[4])] = numpy.random.randint(255)
        self.dataMgr[self.dataMgr._activeImageNumber].Connected_Components.setInputOverlay(threshold_ov)
        
        self.testThread = TestThread(self.connectedComponentsMgr, listOfResultOverlays, listOfFilenames)
        QtCore.QObject.connect(self.testThread, QtCore.SIGNAL('done()'), self.finalizeTest)
        self.testThread.start(None) # ...compute connected components without background

    def finalizeTest(self):
        # results comparison
        self.assertEqual(self.testThread.passedTest, False) # has to be different from ground truth result (wrong input data!)
        self.app.quit()
        
class zzzTestDummy(unittest.TestCase): 
     
    def test_dummy(self):
        pass
        
    def tearDown(self):
        jobMachine.GLOBAL_WM.stopWorkers()

if __name__ == "__main__":
    unittest.main()
    jobMachine.GLOBAL_WM.stopWorkers()


