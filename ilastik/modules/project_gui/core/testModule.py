from ilastik.core import projectClass
import unittest
import glob
from ilastik.core.testThread import TestHelperFunctions

class Tests(unittest.TestCase):
    
    def setUp(self):
        #self.app = QtCore.QCoreApplication(sys.argv)
        self.testdir = "../../../../testdata/"
        
        print "setUp"
        
    def tearDown(self):
        print "tearDown"
        #jobMachine.GLOBAL_WM.stopWorkers()
    
    def test_AddFile(self):
        project = projectClass.Project("test", "test", "test")
        
        fileList = [str(self.testdir + "colorballs.jpg"), str(self.testdir + "zebra.jpg")]
        #fileList = [str(self.testdir + "zebra.jpg"), str(self.testdir + "zebra.jpg")]
        project.addFile(fileList)
        print str(self.testdir + "test_two_images.ilp")
        print str(self.testdir + "syswywy.ilp")
        project.saveToDisk(str(self.testdir + "test_two_images.ilp"))
        same = TestHelperFunctions.compareH5Files(str(self.testdir + "test_two_images.ilp"), 
                                           str(self.testdir + "syswywy.ilp"))
        self.assertEqual(same, True)
        
        
if __name__ == "__main__":
    unittest.main()
        