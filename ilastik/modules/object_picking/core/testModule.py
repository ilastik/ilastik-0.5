import sys
from ilastik.core.projectClass import Project
from ilastik.modules.object_picking.core.objectModuleMgr import ObjectPickingModuleMgr
import unittest
from ilastik.core.testThread import TestHelperFunctions
from ilastik.core import dataImpex
from ilastik.core import jobMachine
from ilastik.core.overlays import selectionOverlay
from ilastik import __path__ as ilastikpath
import numpy, copy

from ilastik.core.testThread import setUp, tearDown
#*******************************************************************************
# fakeVolumeUpdate                                                             *
#*******************************************************************************

class fakeVolumeUpdate():
    def __init__(self, data, erasing):
        self.offsets = (0, 0, 0, 0, 0)
        self._data = data
        self.sizes = data.shape
        self.erasing = erasing

#*******************************************************************************
# Object T e s t P r o j e c t                                                 *
#*******************************************************************************
class ObjectTestProject(object):
    # this class is used to set up a default project which is then used for testing functionality, 
    # hopefully, this will reduce code redundancy
    def __init__(self, cc_filename, labeloverlay_filename, groundtruth_filename):
        
        self.cc_filename = cc_filename
        self.labeloverlay_filename = labeloverlay_filename
        self.groundtruth_filename = groundtruth_filename
        
        self.testdir = ilastikpath[0] + "/testdata/object_picking/"
        
        # create project
        self.project = Project('Project Name', 'Labeler', 'Description')
        self.dataMgr = self.project.dataMgr
    
        # create file list and load data
        path = str(self.testdir + self.cc_filename) # the image is not really used since we load the threshold overlay from a file, however, we need it to set the correct dimensions 
        fileList = []
        fileList.append(path)
        self.project.addFile(fileList)
        
        # create object picking manager
        self.objectPickingMgr = ObjectPickingModuleMgr(self.dataMgr)
    
        # setup inputs
        self.inputOverlays = []
        #self.inputOverlays.append(self.dataMgr[self.dataMgr._activeImageNumber].overlayMgr["Raw Data"])
        
        # load connected components from the same file
        self.label_ov = dataImpex.DataImpex.importOverlay(self.dataMgr[self.dataMgr._activeImageNumber], str(self.testdir + self.labeloverlay_filename), "")        
        self.fvu = fakeVolumeUpdate(self.label_ov._data._data, erasing=False)
        self.cc_ov = dataImpex.DataImpex.importOverlay(self.dataMgr[self.dataMgr._activeImageNumber], str(self.testdir + self.cc_filename), "")
        self.dataMgr[self.dataMgr._activeImageNumber].Object_Picking.setInputData(self.cc_ov._data)    
        ov = selectionOverlay.SelectionOverlay(self.cc_ov._data, color = 4278255615)
        self.dataMgr[self.dataMgr._activeImageNumber].overlayMgr["Objects/Selection Result"] = ov
        #ground truth
        #self.
        
        # overlay lists and filenames
        self.listOfResultOverlays = []
        self.listOfFilenames = []
        self.listOfResultOverlays.append("Objects/Selection Result")
        self.listOfFilenames.append(self.testdir + self.groundtruth_filename)
        
#*******************************************************************************
# TestObjectLabels                                                             *
#*******************************************************************************
class TestObjectLabels(unittest.TestCase):
    def setUp(self):
        print "TestObjectLabels, setUp"
        self.testProject = ObjectTestProject("cc_ov.h5", "label_ov.h5", "selection_result.h5")
        
    def test(self):
        #test the object selection results from labels from a file
        try:
            fakelabellist = []
            fakelabellist.append(self.testProject.fvu)
            self.testProject.dataMgr[self.testProject.dataMgr._activeImageNumber].Object_Picking.newLabels(fakelabellist)
            if self.testProject.dataMgr[self.testProject.dataMgr._activeImageNumber].overlayMgr["Objects/Selection Result"] is None:                
                self.finalize(False)
            else:
                rv = TestHelperFunctions.compareResultsWithFile(self.testProject, self.testProject.listOfResultOverlays, self.testProject.listOfFilenames, tolerance = 0)
                self.finalize(rv)
        except Exception, e:
            print e
            self.finalize(False)        
        
    def finalize(self, returnValue):
        self.assertEqual(returnValue, True)        
        jobMachine.GLOBAL_WM.stopWorkers()

#*******************************************************************************
# TestObjectSelectAll_1                                                        *
#*******************************************************************************        
class TestObjectSelectAll_1(unittest.TestCase):
    def setUp(self):
        print "TestObjectSelectAll, setUp"
        self.testProject = ObjectTestProject("cc_ov.h5", "all_labels_ov.h5", "all_selection_result.h5")
        
    def test(self):
        #test the "selectAll" and "clearAll" functions
        self.testProject.dataMgr[self.testProject.dataMgr._activeImageNumber].Object_Picking.selectAll()
        if self.testProject.dataMgr[self.testProject.dataMgr._activeImageNumber].overlayMgr["Objects/Selection Result"] is None:                
            self.finalize(False)
        else:
            rv = TestHelperFunctions.compareResultsWithFile(self.testProject, self.testProject.listOfResultOverlays, self.testProject.listOfFilenames, tolerance = 0)
            if rv:
                self.testProject.dataMgr[self.testProject.dataMgr._activeImageNumber].Object_Picking.clearAll()
                data = self.testProject.dataMgr[self.testProject.dataMgr._activeImageNumber].overlayMgr["Objects/Selection Result"][:]
                if len(numpy.nonzero(data)[0])!=0:
                    self.finalize(False)
                else:
                    self.finalize(True)
            else:
                self.finalize(False)
            
    def finalize(self, returnValue):
        self.assertEqual(returnValue, True)        
        jobMachine.GLOBAL_WM.stopWorkers()

#*******************************************************************************
# TestObjectSelectAll_2                                                        *
#*******************************************************************************                
class TestObjectSelectAll_2(unittest.TestCase):
    def setUp(self):
        print "TestObjectSelectAll2, setUp"
        self.testProject = ObjectTestProject("cc_ov.h5", "all_labels_ov.h5", "all_selection_result.h5")
        
    def test(self):
        #check, that the set of selected values is correct for setting labels and calling selectAll directly    
        fakelabellist = []
        fakelabellist.append(self.testProject.fvu)
        self.testProject.dataMgr[self.testProject.dataMgr._activeImageNumber].Object_Picking.newLabels(fakelabellist)
        selection1 = copy.deepcopy(self.testProject.dataMgr[self.testProject.dataMgr._activeImageNumber].Object_Picking.selectedObjects.values())
        self.testProject.dataMgr[self.testProject.dataMgr._activeImageNumber].Object_Picking.clearAll()
        self.testProject.dataMgr[self.testProject.dataMgr._activeImageNumber].Object_Picking.selectAll()
        selection2 = self.testProject.dataMgr[self.testProject.dataMgr._activeImageNumber].Object_Picking.selectedObjects.values()
        if selection1 != selection2:
            self.finalize(False)
        else:
            self.finalize(True)
            
            
    def finalize(self, returnValue):
        self.assertEqual(returnValue, True)        
        jobMachine.GLOBAL_WM.stopWorkers()
        
#*******************************************************************************
# TestRemoveLabels                                                             *
#*******************************************************************************                       
class TestRemoveLabels(unittest.TestCase):
    def setUp(self):
        print "TestRemoveLabels setUp"
        self.testProject = ObjectTestProject("cc_ov.h5", "label_ov.h5", "remove_selection_result.h5")
        
    def test(self):
        remove_fvu = fakeVolumeUpdate(self.testProject.fvu._data, erasing=True)
        fakelabellist = []
        fakelabellist.append(remove_fvu)
        self.testProject.dataMgr[self.testProject.dataMgr._activeImageNumber].Object_Picking.selectAll()
        self.testProject.dataMgr[self.testProject.dataMgr._activeImageNumber].Object_Picking.newLabels(fakelabellist)
        if self.testProject.dataMgr[self.testProject.dataMgr._activeImageNumber].overlayMgr["Objects/Selection Result"] is None:                
            self.finalize(False)
        else:
            rv = TestHelperFunctions.compareResultsWithFile(self.testProject, self.testProject.listOfResultOverlays, self.testProject.listOfFilenames, tolerance = 0)
            self.finalize(rv)
            
    def finalize(self, returnValue):
        self.assertEqual(returnValue, True)
        jobMachine.GLOBAL_WM.stopWorkers()
             
#*******************************************************************************
# TestObjectExtraction                                                         *
#*******************************************************************************          
class TestObjectExtraction(unittest.TestCase):
    def setUp(self):
        print "TestObjectExtraction setUp"
        self.testProject = ObjectTestProject("cc_ov.h5", "label_ov.h5", "selection_result.h5")
        
    def test(self):
        fakelabellist = []
        fakelabellist.append(self.testProject.fvu)
        self.testProject.dataMgr[self.testProject.dataMgr._activeImageNumber].Object_Picking.newLabels(fakelabellist)
        objs = self.testProject.dataMgr[self.testProject.dataMgr._activeImageNumber].Object_Picking.objectsSlow3d(self.testProject.cc_ov)
        for obj, coords in objs.items():
            v = obj
            for i in range(len(coords[0])):
                if self.testProject.cc_ov[0, coords[0][i], coords[1][i], coords[2][i], 0]!=v:
                    self.finalize(False)
                
    def finalize(self, returnValue):
        self.assertEqual(returnValue, True)        
        jobMachine.GLOBAL_WM.stopWorkers()
                
class TestObjectExtractionFail(unittest.TestCase):
    def setUp(self):
        print "TestObjectExtractionFail setUp"
        self.testProject = ObjectTestProject("cc_ov.h5", "label_ov.h5", "selection_result.h5")
        
    def test(self):
        fakelabellist = []
        fakelabellist.append(self.testProject.fvu)
        self.testProject.dataMgr[self.testProject.dataMgr._activeImageNumber].Object_Picking.newLabels(fakelabellist)
        objs = self.testProject.dataMgr[self.testProject.dataMgr._activeImageNumber].Object_Picking.objectsSlow3d(self.testProject.cc_ov)
        for obj, coords in objs.items():
            v = obj+1
            for i in range(len(coords[0])):
                if self.testProject.cc_ov[0, coords[0][i], coords[1][i], coords[2][i], 0]!=v:
                    self.finalize(False)
                
    def finalize(self, returnValue):
        self.assertEqual(returnValue, False)        
        jobMachine.GLOBAL_WM.stopWorkers()                
#*******************************************************************************
# i f   _ _ n a m e _ _   = =   " _ _ m a i n _ _ "                            *
#*******************************************************************************

if __name__ == "__main__":
    unittest.main()       
        