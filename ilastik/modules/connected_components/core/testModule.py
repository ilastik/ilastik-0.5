from PyQt4 import QtCore
import sys
from ilastik.core.projectClass import Project
from ilastik.modules.connected_components.core.connectedComponentsMgr import ConnectedComponentsModuleMgr
import unittest
from ilastik.core.testThread import TestThread
from ilastik.core import dataImpex
from ilastik.core import jobMachine
from ilastik import __path__ as ilastikpath

#*******************************************************************************
# C C T e s t P r o j e c t                                                    *
#*******************************************************************************

class CCTestProject(object):
    # this class is used to set up a default project which is then used for testing functionality, 
    # hopefully, this will reduced code redundancy
    def __init__(self, image_filename, thresholdoverlay_filename, groundtruth_filename):
        
        self.image_filename = image_filename
        self.thresholdoverlay_filename = thresholdoverlay_filename
        self.groundtruth_filename = groundtruth_filename
        
        self.testdir = ilastikpath[0] + "/testdata/connected_components/"
        
        # create project
        self.project = Project('Project Name', 'Labeler', 'Description')
        self.dataMgr = self.project.dataMgr
    
        # create file list and load data
        path = str(self.testdir + self.image_filename) # the image is not really used since we load the threshold overlay from a file, however, we need it to set the correct dimensions 
        fileList = []
        fileList.append(path)
        self.project.addFile(fileList)
        
        # create automatic segmentation manager
        self.connectedComponentsMgr = ConnectedComponentsModuleMgr(self.dataMgr)
    
        # setup inputs
        self.inputOverlays = []
        self.inputOverlays.append(self.dataMgr[self.dataMgr._activeImageNumber].overlayMgr["Raw Data"])
        
        # load precalculated threshold overlay from file
        self.threshold_ov = dataImpex.DataImpex.importOverlay(self.dataMgr[self.dataMgr._activeImageNumber], str(self.testdir + self.thresholdoverlay_filename), "")
        self.dataMgr[self.dataMgr._activeImageNumber].Connected_Components.setInputData(self.threshold_ov._data)    
        
        # overlay lists and filenames
        self.listOfResultOverlays = []
        self.listOfFilenames = []
        self.listOfResultOverlays.append("Connected Components/CC Results")
        self.listOfFilenames.append(self.testdir + self.groundtruth_filename)

#*******************************************************************************
# T e s t W h o l e M o d u l e _ W i t h o u t B a c k g r o u n d            *
#*******************************************************************************

class TestWholeModule_WithoutBackground(unittest.TestCase):
     
    def setUp(self):
        #print "setUp"
        self.app = QtCore.QCoreApplication(sys.argv) # we need a QCoreApplication to run, otherwise the thread just gets killed
        self.testProject = CCTestProject("test_image.png", "cc_threshold_overlay.h5", "ground_truth_cc_without_background.h5")
    
    def test_WholeModule(self):
        t = QtCore.QTimer()
        t.setSingleShot(True)
        t.setInterval(0)
        self.app.connect(t, QtCore.SIGNAL('timeout()'), self.mainFunction)        
        t.start()
        self.app.exec_()
        
    def mainFunction(self):
        self.testThread = TestThread(self.testProject.connectedComponentsMgr, self.testProject.listOfResultOverlays, self.testProject.listOfFilenames)
        QtCore.QObject.connect(self.testThread, QtCore.SIGNAL('done()'), self.finalizeTest)
        self.testThread.start(None) # ...compute connected components without background

    def finalizeTest(self):
        # results comparison
        self.assertEqual(self.testThread.passedTest, True)
        self.app.quit()


#*******************************************************************************
# T e s t W h o l e M o d u l e _ W i t h o u t B a c k g r o u n d W r o n g I m a g e *
#*******************************************************************************

class TestWholeModule_WithoutBackgroundWrongImage(unittest.TestCase): # tests if wrong input leads to a test fail
     
    def setUp(self):
        #print "setUp"
        self.app = QtCore.QCoreApplication(sys.argv) # we need a QCoreApplication to run, otherwise the thread just gets killed
        self.testProject = CCTestProject("test_image_mirrored.png", "cc_threshold_overlay.h5", "ground_truth_cc_without_background.h5")
    
    def test_WholeModule(self):
        t = QtCore.QTimer()
        t.setSingleShot(True)
        t.setInterval(0)
        self.app.connect(t, QtCore.SIGNAL('timeout()'), self.mainFunction)        
        t.start()
        self.app.exec_()
        
    def mainFunction(self):
        # ...randomly exchange some pixels
        import numpy
        for i in range(10):
            self.testProject.threshold_ov._data._data[numpy.random.randint(self.testProject.threshold_ov._data._data.shape[0]), numpy.random.randint(self.testProject.threshold_ov._data._data.shape[1]), numpy.random.randint(self.testProject.threshold_ov._data._data.shape[2]), numpy.random.randint(self.testProject.threshold_ov._data._data.shape[3]), numpy.random.randint(self.testProject.threshold_ov._data._data.shape[4])] = numpy.random.randint(255)
        self.testProject.dataMgr[self.testProject.dataMgr._activeImageNumber].Connected_Components.setInputData(self.testProject.threshold_ov._data)
        
        self.testThread = TestThread(self.testProject.connectedComponentsMgr, self.testProject.listOfResultOverlays, self.testProject.listOfFilenames)
        QtCore.QObject.connect(self.testThread, QtCore.SIGNAL('done()'), self.finalizeTest)
        self.testThread.start(None) # ...compute connected components without background

    def finalizeTest(self):
        # results comparison
        self.assertEqual(self.testThread.passedTest, False) # has to be different from ground truth result (wrong input data!)
        self.app.quit()
        
        
#*******************************************************************************
# T e s t W h o l e M o d u l e _ W i t h B a c k g r o u n d 1                *
#*******************************************************************************

class TestWholeModule_WithBackground1(unittest.TestCase):
     
    def setUp(self):
        #print "setUp"
        self.app = QtCore.QCoreApplication(sys.argv) # we need a QCoreApplication to run, otherwise the thread just gets killed
        self.testProject = CCTestProject("test_image.png", "cc_threshold_overlay.h5", "ground_truth_cc_with_background.h5")
    
    def test_WholeModule(self):
        t = QtCore.QTimer()
        t.setSingleShot(True)
        t.setInterval(0)
        self.app.connect(t, QtCore.SIGNAL('timeout()'), self.mainFunction)        
        t.start()
        self.app.exec_()
        
    def mainFunction(self):
        self.testThread = TestThread(self.testProject.connectedComponentsMgr, self.testProject.listOfResultOverlays, self.testProject.listOfFilenames)
        QtCore.QObject.connect(self.testThread, QtCore.SIGNAL('done()'), self.finalizeTest)
        backgroundClasses = set([5, 6]) # use a non-empty background set
        self.testThread.start(backgroundClasses) # ...compute connected components with background

    def finalizeTest(self):
        # results comparison
        self.assertEqual(self.testThread.passedTest, True)
        self.app.quit()
 
#*******************************************************************************
# T e s t W h o l e M o d u l e _ W i t h B a c k g r o u n d 2                *
#*******************************************************************************

class TestWholeModule_WithBackground2(unittest.TestCase):
     
    def setUp(self):
        #print "setUp"
        self.app = QtCore.QCoreApplication(sys.argv) # we need a QCoreApplication to run, otherwise the thread just gets killed
        self.testProject = CCTestProject("test_image.png", "cc_threshold_overlay.h5", "ground_truth_cc_without_background.h5")
    
    def test_WholeModule(self):
        t = QtCore.QTimer()
        t.setSingleShot(True)
        t.setInterval(0)
        self.app.connect(t, QtCore.SIGNAL('timeout()'), self.mainFunction)        
        t.start()
        self.app.exec_()
        
    def mainFunction(self):
        self.testThread = TestThread(self.testProject.connectedComponentsMgr, self.testProject.listOfResultOverlays, self.testProject.listOfFilenames)
        QtCore.QObject.connect(self.testThread, QtCore.SIGNAL('done()'), self.finalizeTest)
        backgroundClasses = set([]) # use an empty background set - should then equal result without background
        self.testThread.start(backgroundClasses) # ...compute connected components with background

    def finalizeTest(self):
        # results comparison
        self.assertEqual(self.testThread.passedTest, True)
        self.app.quit()
                
#*******************************************************************************
# z z z T e s t D u m m y                                                      *
#*******************************************************************************

class zzzTestDummy(unittest.TestCase): 
     
    def test_dummy(self):
        pass
        
    def tearDown(self):
        jobMachine.GLOBAL_WM.stopWorkers()

#*******************************************************************************
# i f   _ _ n a m e _ _   = =   " _ _ m a i n _ _ "                            *
#*******************************************************************************

if __name__ == "__main__":
    unittest.main()
    jobMachine.GLOBAL_WM.stopWorkers()


