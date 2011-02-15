from ilastik.core.projectClass import Project
from ilastik.core.testThread import TestHelperFunctions
from ilastik.modules.automatic_segmentation.core.automaticSegmentationMgr import AutomaticSegmentationModuleMgr
import unittest
from ilastik.core import dataImpex
from ilastik.core import jobMachine
from ilastik import __path__ as ilastikpath

class TestWholeModule(unittest.TestCase):
     
    def setUp(self):
        #print "setUp"
        self.testdir = ilastikpath[0] + "/testdata/automatic_segmentation/"
    
    def test_WholeModule(self):
        # create project
        self.project = Project('Project Name', 'Labeler', 'Description')
        self.dataMgr = self.project.dataMgr
    
        # create file list and load data
        path = str(self.testdir + "test_image.png")    
        fileList = []
        fileList.append(path)
        self.project.addFile(fileList)
        
        # create automatic segmentation manager
        self.automaticSegmentationMgr = AutomaticSegmentationModuleMgr(self.dataMgr)
    
        # setup inputs, compute results
        inputOverlays = []
        inputOverlays.append(self.dataMgr[self.dataMgr._activeImageNumber].overlayMgr["Raw Data"])
        
        # load precalculated border indicators from file (we use precalculated border indicators since we want to avoid dependencies between the feature module and this one)
        dataImpex.DataImpex.importOverlay(self.dataMgr[self.dataMgr._activeImageNumber], str(self.testdir + "borders_gaussianGradientMagnitude_sigma0.3_channel2.h5"), "")
        
        # overlay lists and filenames
        listOfResultOverlays = []
        listOfFilenames = []
        listOfResultOverlays.append("Auto Segmentation/Segmentation")
        listOfFilenames.append(self.testdir + "ground_truth_auto_segmentation.h5")
        
        # calculate segmentation results
        # ...import border indicator
        border_indicator_ov = self.dataMgr[self.dataMgr._activeImageNumber].overlayMgr["border_ind"]
        input = border_indicator_ov._data[0,:,:,:,0]
        # ...normalize it
        input = self.automaticSegmentationMgr.normalizePotential(input)
        # ...invert it twice, this should give us the original again :-)
        input = self.automaticSegmentationMgr.invertPotential(input)
        input = self.automaticSegmentationMgr.invertPotential(input)
        # ...compute results
        self.automaticSegmentationMgr.computeResults(input)
        # ...add overlays
        self.automaticSegmentationMgr.finalizeResults()
        
        # compare obtained result to ground truth result
        equalOverlays = TestHelperFunctions.compareResultsWithFile(self.automaticSegmentationMgr, listOfResultOverlays, listOfFilenames)
        self.assertEqual(equalOverlays, True)
        
class TestWholeModuleWrongImage(unittest.TestCase): # this test tests if wrong input data leads to wrong results
     
    def setUp(self):
        #print "setUp"
        self.testdir = ilastikpath[0] + "/testdata/automatic_segmentation/"
    
    def test_WholeModule(self):
        # create project
        self.project = Project('Project Name', 'Labeler', 'Description')
        self.dataMgr = self.project.dataMgr
    
        # create file list and load data
        path = str(self.testdir + "test_image_mirrored.png")    
        fileList = []
        fileList.append(path)
        self.project.addFile(fileList)
        
        # create automatic segmentation manager
        self.automaticSegmentationMgr = AutomaticSegmentationModuleMgr(self.dataMgr)
    
        # setup inputs, compute results
        inputOverlays = []
        inputOverlays.append(self.dataMgr[self.dataMgr._activeImageNumber].overlayMgr["Raw Data"])
        
        # load precalculated border indicators from file (we use precalculated border indicators since we want to avoid dependencies between the feature module and this one)
        dataImpex.DataImpex.importOverlay(self.dataMgr[self.dataMgr._activeImageNumber], str(self.testdir + "borders_gaussianGradientMagnitude_sigma0.3_channel2_mirrored.h5"), "")
        
        # overlay lists and filenames
        listOfResultOverlays = []
        listOfFilenames = []
        listOfResultOverlays.append("Auto Segmentation/Segmentation")
        listOfFilenames.append(self.testdir + "ground_truth_auto_segmentation.h5")
        
        # calculate segmentation results
        # ...import border indicator
        border_indicator_ov = self.dataMgr[self.dataMgr._activeImageNumber].overlayMgr["border_ind"]
        input = border_indicator_ov._data[0,:,:,:,0]
        # ...normalize it
        input = self.automaticSegmentationMgr.normalizePotential(input)
        # ...invert it twice, this should give us the original again :-)
        input = self.automaticSegmentationMgr.invertPotential(input)
        input = self.automaticSegmentationMgr.invertPotential(input)
        # ...compute results
        self.automaticSegmentationMgr.computeResults(input)
        # ...add overlays
        self.automaticSegmentationMgr.finalizeResults()
        
        # compare obtained result to ground truth result
        equalOverlays = TestHelperFunctions.compareResultsWithFile(self.automaticSegmentationMgr, listOfResultOverlays, listOfFilenames)
        self.assertEqual(equalOverlays, False)        
        
class zzzTestDummy(unittest.TestCase): 
     
    def test_dummy(self):
        pass
        
    def tearDown(self):
        jobMachine.GLOBAL_WM.stopWorkers()   

if __name__ == "__main__":
    unittest.main()
    jobMachine.GLOBAL_WM.stopWorkers()


