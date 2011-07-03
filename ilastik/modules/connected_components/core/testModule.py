#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    Copyright 2010, 2011 C Sommer, C Straehle, U Koethe, FA Hamprecht. All rights reserved.
#    
#    Redistribution and use in source and binary forms, with or without modification, are
#    permitted provided that the following conditions are met:
#    
#       1. Redistributions of source code must retain the above copyright notice, this list of
#          conditions and the following disclaimer.
#    
#       2. Redistributions in binary form must reproduce the above copyright notice, this list
#          of conditions and the following disclaimer in the documentation and/or other materials
#          provided with the distribution.
#    
#    THIS SOFTWARE IS PROVIDED BY THE ABOVE COPYRIGHT HOLDERS ``AS IS'' AND ANY EXPRESS OR IMPLIED
#    WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
#    FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE ABOVE COPYRIGHT HOLDERS OR
#    CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#    CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#    SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
#    ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#    NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
#    ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#    
#    The views and conclusions contained in the software and documentation are those of the
#    authors and should not be interpreted as representing official policies, either expressed
#    or implied, of their employers.

from PyQt4.QtCore import QCoreApplication, QObject, QTimer, SIGNAL

import sys
from ilastik.core.projectClass import Project
from ilastik.modules.connected_components.core.connectedComponentsMgr import ConnectedComponentsModuleMgr
import unittest
from ilastik.core.testThread import TestThread
from ilastik.core import dataImpex
from ilastik.core import jobMachine
from ilastik import __path__ as ilastikpath

from ilastik.core.testThread import setUp, tearDown

#*******************************************************************************
# C C T e s t P r o j e c t                                                    *
#*******************************************************************************

class CCTestProject(object):
    # this class is used to set up a default project which is then used for testing functionality, 
    # hopefully, this will reduce code redundancy
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
        
        # create connected components manager
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
# T e s t W h o l e M o d u l e _ W i t h o u t B a c k g r o u n d 2 D        *
#*******************************************************************************

class TestWholeModule_WithoutBackground2D(unittest.TestCase):
     
    def setUp(self):
        print "setUp"
        self.app = QCoreApplication(sys.argv) # we need a QCoreApplication to run, otherwise the thread just gets killed
        self.testProject = CCTestProject("test_image.png", "cc_threshold_overlay.h5", "ground_truth_cc_without_background.h5")
    
    def test_WholeModule(self):
        t = QTimer()
        t.setSingleShot(True)
        t.setInterval(0)
        self.app.connect(t, SIGNAL('timeout()'), self.mainFunction)        
        t.start()
        self.app.exec_()
        
    def mainFunction(self):
        self.testThread = TestThread(self.testProject.connectedComponentsMgr, self.testProject.listOfResultOverlays, self.testProject.listOfFilenames)
        QObject.connect(self.testThread, SIGNAL('done()'), self.finalizeTest)
        self.testThread.start(None) # ...compute connected components without background

    def finalizeTest(self):
        # results comparison
        print "finalize"
        self.assertEqual(self.testThread.passedTest, True)
        self.app.quit()

#*******************************************************************************
# T e s t W h o l e M o d u l e _ W i t h o u t B a c k g r o u n d W r o n g I m a g e 2 D*
#*******************************************************************************

class TestWholeModule_WithoutBackgroundWrongImage2D(unittest.TestCase): # tests if wrong input leads to a test fail
     
    def setUp(self):
        #print "setUp"
        self.app = QCoreApplication(sys.argv) # we need a QCoreApplication to run, otherwise the thread just gets killed
        self.testProject = CCTestProject("test_image_mirrored.png", "cc_threshold_overlay.h5", "ground_truth_cc_without_background.h5")
    
    def test_WholeModule(self):
        t = QTimer()
        t.setSingleShot(True)
        t.setInterval(0)
        self.app.connect(t, SIGNAL('timeout()'), self.mainFunction)        
        t.start()
        self.app.exec_()
        
    def mainFunction(self):
        # ...randomly exchange some pixels
        import numpy
        for i in range(10):
            self.testProject.threshold_ov._data._data[numpy.random.randint(self.testProject.threshold_ov._data._data.shape[0]), numpy.random.randint(self.testProject.threshold_ov._data._data.shape[1]), numpy.random.randint(self.testProject.threshold_ov._data._data.shape[2]), numpy.random.randint(self.testProject.threshold_ov._data._data.shape[3]), numpy.random.randint(self.testProject.threshold_ov._data._data.shape[4])] = numpy.random.randint(255)
        self.testProject.dataMgr[self.testProject.dataMgr._activeImageNumber].Connected_Components.setInputData(self.testProject.threshold_ov._data)
        
        self.testThread = TestThread(self.testProject.connectedComponentsMgr, self.testProject.listOfResultOverlays, self.testProject.listOfFilenames)
        QObject.connect(self.testThread, SIGNAL('done()'), self.finalizeTest)
        self.testThread.start(None) # ...compute connected components without background

    def finalizeTest(self):
        # results comparison
        self.assertEqual(self.testThread.passedTest, False) # has to be different from ground truth result (wrong input data!)
        self.app.quit()
        
        
#*******************************************************************************
# T e s t W h o l e M o d u l e _ W i t h B a c k g r o u n d 2 D 1            *
#*******************************************************************************

class TestWholeModule_WithBackground2D1(unittest.TestCase):
     
    def setUp(self):
        #print "setUp"
        self.app = QCoreApplication(sys.argv) # we need a QCoreApplication to run, otherwise the thread just gets killed
        self.testProject = CCTestProject("test_image.png", "cc_threshold_overlay.h5", "ground_truth_cc_with_background.h5")
    
    def test_WholeModule(self):
        t = QTimer()
        t.setSingleShot(True)
        t.setInterval(0)
        self.app.connect(t, SIGNAL('timeout()'), self.mainFunction)        
        t.start()
        self.app.exec_()
        
    def mainFunction(self):
        self.testThread = TestThread(self.testProject.connectedComponentsMgr, self.testProject.listOfResultOverlays, self.testProject.listOfFilenames)
        QObject.connect(self.testThread, SIGNAL('done()'), self.finalizeTest)
        backgroundClasses = set([5, 6]) # use a non-empty background set
        self.testThread.start(backgroundClasses) # ...compute connected components with background

    def finalizeTest(self):
        # results comparison
        self.assertEqual(self.testThread.passedTest, True)
        self.app.quit()
 
#*******************************************************************************
# T e s t W h o l e M o d u l e _ W i t h B a c k g r o u n d 2 D 2            *
#*******************************************************************************

class TestWholeModule_WithBackground2D2(unittest.TestCase):
     
    def setUp(self):
        #print "setUp"
        self.app = QCoreApplication(sys.argv) # we need a QCoreApplication to run, otherwise the thread just gets killed
        self.testProject = CCTestProject("test_image.png", "cc_threshold_overlay.h5", "ground_truth_cc_without_background.h5")
    
    def test_WholeModule(self):
        t = QTimer()
        t.setSingleShot(True)
        t.setInterval(0)
        self.app.connect(t, SIGNAL('timeout()'), self.mainFunction)        
        t.start()
        self.app.exec_()
        
    def mainFunction(self):
        self.testThread = TestThread(self.testProject.connectedComponentsMgr, self.testProject.listOfResultOverlays, self.testProject.listOfFilenames)
        QObject.connect(self.testThread, SIGNAL('done()'), self.finalizeTest)
        backgroundClasses = set([]) # use an empty background set - should then equal result without background
        self.testThread.start(backgroundClasses) # ...compute connected components with background

    def finalizeTest(self):
        # results comparison
        self.assertEqual(self.testThread.passedTest, True)
        self.app.quit()

#*******************************************************************************
# T e s t W h o l e M o d u l e _ W i t h o u t B a c k g r o u n d 3 D        *
#*******************************************************************************

class TestWholeModule_WithoutBackground3D(unittest.TestCase):
     
    def setUp(self):
        print "setUp"
        self.app = QCoreApplication(sys.argv) # we need a QCoreApplication to run, otherwise the thread just gets killed
        self.testProject = CCTestProject("3dcube2.h5", "3dcube2_cc_threshold_overlay.h5", "3dcube2_ground_truth_cc_without_background.h5")
    
    def test_WholeModule(self):
        t = QTimer()
        t.setSingleShot(True)
        t.setInterval(0)
        self.app.connect(t, SIGNAL('timeout()'), self.mainFunction)        
        t.start()
        self.app.exec_()
        
    def mainFunction(self):
        self.testThread = TestThread(self.testProject.connectedComponentsMgr, self.testProject.listOfResultOverlays, self.testProject.listOfFilenames)
        QObject.connect(self.testThread, SIGNAL('done()'), self.finalizeTest)
        self.testThread.start(None) # ...compute connected components without background

    def finalizeTest(self):
        # results comparison
        print "finalize"
        self.assertEqual(self.testThread.passedTest, True)
        self.app.quit()

#*******************************************************************************
# T e s t W h o l e M o d u l e _ W i t h B a c k g r o u n d 3 D              *
#*******************************************************************************

class TestWholeModule_WithBackground3D(unittest.TestCase):
     
    def setUp(self):
        #print "setUp"
        self.app = QCoreApplication(sys.argv) # we need a QCoreApplication to run, otherwise the thread just gets killed
        self.testProject = CCTestProject("3dcube2.h5", "3dcube2_cc_threshold_overlay.h5", "3dcube2_ground_truth_cc_with_background.h5")
    
    def test_WholeModule(self):
        t = QTimer()
        t.setSingleShot(True)
        t.setInterval(0)
        self.app.connect(t, SIGNAL('timeout()'), self.mainFunction)        
        t.start()
        self.app.exec_()
        
    def mainFunction(self):
        self.testThread = TestThread(self.testProject.connectedComponentsMgr, self.testProject.listOfResultOverlays, self.testProject.listOfFilenames)
        QObject.connect(self.testThread, SIGNAL('done()'), self.finalizeTest)
        backgroundClasses = set([1, 3]) # use a non-empty background set
        self.testThread.start(backgroundClasses) # ...compute connected components with background

    def finalizeTest(self):
        # results comparison
        self.assertEqual(self.testThread.passedTest, True)
        self.app.quit()
 
 
#*******************************************************************************
# i f   _ _ n a m e _ _   = =   " _ _ m a i n _ _ "                            *
#*******************************************************************************

if __name__ == "__main__":
    unittest.main()


