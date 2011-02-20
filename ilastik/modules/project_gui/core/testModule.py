from ilastik.core import projectClass
import unittest
import glob
from ilastik.core.testThread import TestHelperFunctions
from ilastik import __path__ as ilastikpath

#*******************************************************************************
# T e s t s                                                                    *
#*******************************************************************************

class Tests(unittest.TestCase):
    
    def setUp(self):
        #self.app = QtCore.QCoreApplication(sys.argv)
        
        self.testdir = ilastikpath[0] + "/testdata/project_gui/"
        self.outputfile = self.testdir + "test_two_images.ilp"
        self.groundtruthfile = self.testdir + "gt_two_images.ilp"
        print self.testdir
        print "setUp"
        
    def tearDown(self):
        print "tearDown"
        #jobMachine.GLOBAL_WM.stopWorkers()
    
    def test_AddFile(self):
        project = projectClass.Project("test", "test", "test")
        
        fileList = [str(self.testdir + "colorballs.png"), str(self.testdir + "zebra.png")]
        #fileList = [str(self.testdir + "zebra.jpg"), str(self.testdir + "zebra.jpg")]
        project.addFile(fileList)
        project.saveToDisk(self.outputfile)
        same = TestHelperFunctions.compareH5Files(self.outputfile, self.groundtruthfile)
        print "test add file result: ", same
        self.assertEqual(same, True)
        
        
#*******************************************************************************
# i f   _ _ n a m e _ _   = =   " _ _ m a i n _ _ "                            *
#*******************************************************************************

if __name__ == "__main__":
    unittest.main()
        