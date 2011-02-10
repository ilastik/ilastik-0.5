from ilastik.core import projectClass
import unittest
import glob
from ilastik.core.testThread import TestHelperFunctions
from ilastik import __path__ as ilastikpath

class Tests(unittest.TestCase):
    
    def setUp(self):
        #self.app = QtCore.QCoreApplication(sys.argv)
        self.testdir = ilastikpath[0] + "/testdata/"
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
        print str(self.testdir + "test_two_images.ilp")
        print str(self.testdir + "gt_two_images.ilp")
        project.saveToDisk(str(self.testdir + "test_two_images.ilp"))
        same = TestHelperFunctions.compareH5Files(str("test_two_images.ilp"), 
                                           str("gt_two_images.ilp"))
        self.assertEqual(same, True)
        
        
if __name__ == "__main__":
    unittest.main()
        