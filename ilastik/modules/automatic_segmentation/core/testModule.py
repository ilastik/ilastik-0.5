from ilastik.core.projectClass import Project
from ilastik.core.testThread import TestHelperFunctions
from ilastik.modules.automatic_segmentation.core.automaticSegmentationMgr import AutomaticSegmentationModuleMgr
import unittest
from ilastik.core import dataImpex
from ilastik.core import jobMachine
from ilastik import __path__ as ilastikpath

#*******************************************************************************
# A u t o m a t i c S e g m e n t a t i o n T e s t P r o j e c t              *
#*******************************************************************************

class AutomaticSegmentationTestProject(object):
    # this class is used to set up a default project which is then used for testing functionality, 
    # hopefully, this will reduced code redundancy
    def __init__(self, image_filename, borderOverlay_filename, groundtruth_filename):
        
        self.image_filename = image_filename
        self.borderOverlay_filename = borderOverlay_filename
        self.groundtruth_filename = groundtruth_filename
        
        self.testdir = ilastikpath[0] + "/testdata/automatic_segmentation/"
        
        # create project
        self.project = Project('Project Name', 'Labeler', 'Description')
        self.dataMgr = self.project.dataMgr
    
        # create file list and load data
        path = str(self.testdir + self.image_filename) # the image is not really used since we load the threshold overlay from a file, however, we need it to set the correct dimensions 
        fileList = []
        fileList.append(path)
        self.project.addFile(fileList)
        
        # create automatic segmentation manager
        self.automaticSegmentationMgr = AutomaticSegmentationModuleMgr(self.dataMgr)
    
        # setup inputs
        self.inputOverlays = []
        self.inputOverlays.append(self.dataMgr[self.dataMgr._activeImageNumber].overlayMgr["Raw Data"])
        
        # calculate segmentation results
        # ...import border indicator
        self.border_indicator_ov = dataImpex.DataImpex.importOverlay(self.dataMgr[self.dataMgr._activeImageNumber], str(self.testdir + borderOverlay_filename), "")
        self.input = self.border_indicator_ov._data[0,:,:,:,0]
        # ...normalize it
        self.input = self.automaticSegmentationMgr.normalizePotential(self.input)
        # ...invert it twice, this should give us the original again :-)
        self.input = self.automaticSegmentationMgr.invertPotential(self.input)
        self.input = self.automaticSegmentationMgr.invertPotential(self.input)
        
        # overlay lists and filenames
        self.listOfResultOverlays = []
        self.listOfFilenames = []
        self.listOfResultOverlays.append("Auto Segmentation/Segmentation")
        self.listOfFilenames.append(self.testdir + self.groundtruth_filename)
        

#*******************************************************************************
# T e s t W h o l e M o d u l e                                                *
#*******************************************************************************

class TestWholeModule(unittest.TestCase):
     
    def setUp(self):
        #print "setUp"
        self.testProject = AutomaticSegmentationTestProject("test_image.png", "borders_gaussianGradientMagnitude_sigma0.3_channel2.h5", "ground_truth_auto_segmentation.h5")
    
    def test_WholeModule(self):
        # compute results
        self.testProject.automaticSegmentationMgr.computeResults(self.testProject.input)
        # ...add overlays
        self.testProject.automaticSegmentationMgr.finalizeResults()
        
        #obtained = self.testProject.dataMgr[self.testProject.dataMgr._activeImageNumber].overlayMgr[self.testProject.listOfResultOverlays[0]]
        #dataImpex.DataImpex.exportOverlay("c:/new_segmentation_result", "h5", obtained)
        
        # compare obtained result to ground truth result
        equalOverlays = TestHelperFunctions.compareResultsWithFile(self.testProject.automaticSegmentationMgr, self.testProject.listOfResultOverlays, self.testProject.listOfFilenames)
        self.assertEqual(equalOverlays, True)
        
#*******************************************************************************
# T e s t W h o l e M o d u l e W r o n g I m a g e                            *
#*******************************************************************************

class TestWholeModuleWrongImage(unittest.TestCase): # this test tests if wrong input data leads to wrong results
     
    def setUp(self):
        #print "setUp"
        self.testProject = AutomaticSegmentationTestProject("test_image_mirrored.png", "borders_gaussianGradientMagnitude_sigma0.3_channel2_mirrored.h5", "ground_truth_auto_segmentation.h5")
    
    def test_WholeModule(self):
        # compute results
        self.testProject.automaticSegmentationMgr.computeResults(self.testProject.input)
        # ...add overlays
        self.testProject.automaticSegmentationMgr.finalizeResults()
        
        # compare obtained result to ground truth result
        equalOverlays = TestHelperFunctions.compareResultsWithFile(self.testProject.automaticSegmentationMgr, self.testProject.listOfResultOverlays, self.testProject.listOfFilenames)
        self.assertEqual(equalOverlays, False) # has to be different from ground truth result (wrong input data!)
        
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


