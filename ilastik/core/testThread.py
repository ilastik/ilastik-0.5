from PyQt4 import QtCore
import numpy
from ilastik.core import dataImpex
import shlex
from ilastik.core.listOfNDArraysAsNDArray import ListOfNDArraysAsNDArray
from ilastik.core.overlays.selectionOverlay import SelectionAccessor
from subprocess import Popen, PIPE
import h5py

# this is the core replacement of the guiThread used to test module functionality
#*******************************************************************************
# T e s t T h r e a d                                                          *
#*******************************************************************************

import ilastik.core.jobMachine

def setUp():
    if not ilastik.core.jobMachine.GLOBAL_WM:
        ilastik.core.jobMachine.GLOBAL_WM = ilastik.core.jobMachine.WorkerManager()
    
def tearDown():
    ilastik.core.jobMachine.GLOBAL_WM.stopWorkers()
    del ilastik.core.jobMachine.GLOBAL_WM
    ilastik.core.jobMachine.GLOBAL_WM = None

class TestThread(QtCore.QObject):#QtCore.QThread):
    
    def __init__(self, baseMgr, listOfResultOverlays, listOfFilenames, tolerance = 0):
        __pyqtSignals__ = ( "done()")

        #QtCore.QThread.__init__(self, parent)
        QtCore.QObject.__init__(self)
        self.baseMgr = baseMgr
        self.listOfResultOverlays = listOfResultOverlays
        self.listOfFilenames = listOfFilenames
        self.tolerance = tolerance
        self.passedTest = False

    def start(self, input):
        self.timer = QtCore.QTimer()
        QtCore.QObject.connect(self.timer, QtCore.SIGNAL("timeout()"), self.updateProgress)

        # call core function
        self.myTestThread = self.baseMgr.computeResults(input)
        self.timer.start(200)
        
    def updateProgress(self):
        if not self.myTestThread.isRunning():
            self.timer.stop()
            self.myTestThread.wait()
            self.finalize()

    def finalize(self):
        # call core function
        self.baseMgr.finalizeResults()
        # compare obtained results with ground truth results
        self.passedTest = TestHelperFunctions.compareResultsWithFile(self.baseMgr, self.listOfResultOverlays, self.listOfFilenames, self.tolerance)
        # announce that we are done
        self.emit(QtCore.SIGNAL("done()"))
        
        '''
        # in case you want to create ground truth overlays, use the following code instead of the above
        for i in range(len(self.listOfResultOverlays)):
            obtained = self.baseMgr.dataMgr[self.baseMgr.dataMgr._activeImageNumber].overlayMgr["Unsupervised/pLSA component %d" % (i+1)]
            dataImpex.DataImpex.exportOverlay(self.listOfFilenames[i], "h5", obtained)
        '''

#*******************************************************************************
# T e s t H e l p e r F u n c t i o n s                                        *
#*******************************************************************************

class TestHelperFunctions():
    @staticmethod
    def compareResultsWithFile(baseMgr, listOfResultOverlays, listOfFilenames, tolerance = 0):
        equalOverlays = True
        for i in range(len(listOfResultOverlays)):
            obtained = baseMgr.dataMgr[baseMgr.dataMgr._activeImageNumber].overlayMgr[listOfResultOverlays[i]]
            prefix = "Ground_Truth/"
            dataImpex.DataImpex.importOverlay(baseMgr.dataMgr[baseMgr.dataMgr._activeImageNumber], listOfFilenames[i], prefix)
            groundTruth = baseMgr.dataMgr[baseMgr.dataMgr._activeImageNumber].overlayMgr[prefix + listOfResultOverlays[i]]
            equalOverlays = equalOverlays & TestHelperFunctions.compareOverlayData(obtained, groundTruth, tolerance)
        print "all ", str(len(listOfResultOverlays)), " compared overlays are equal: ", equalOverlays
        return equalOverlays        
    
    @staticmethod
    # we only compare the data of the overlay, since we want to avoid dependence on color tables etc.
    def compareOverlayData(overlay1, overlay2, tolerance = 0):
        # overlay1._data._data can be a listOfNDArraysAsNDArray instance, overlay2._data._data is loaded from file, so it should be an NDArray
        if isinstance(overlay1._data._data, ListOfNDArraysAsNDArray):
            datatemp1 = overlay1._data._data.ndarrays
        elif isinstance(overlay1._data._data, SelectionAccessor):
            datatemp1 = overlay1._data._data[:]
        else:
            datatemp1 = overlay1._data._data 
        datatemp2 = overlay2._data._data
        
        if numpy.all(numpy.abs(datatemp1 - datatemp2) <= tolerance):
            return True
        else: 
            return False
    @staticmethod
    def arrayEqual(a,b):
        assert a.shape == b.shape
        assert a.dtype == b.dtype
        if not numpy.array_equal(a,b):
            assert len(a.shape) == 3
            for x in range(a.shape[0]):
                for y in range(a.shape[1]):
                    for z in range(a.shape[2]):
                        if a[x,y,z] != b[x,y,z]:
                            print x,y,z, "a=", a[x,y,z], "b=", b[x,y,z]
            return False
        return True
        
    @staticmethod
    def compareH5Files(file1, file2):
        print "files to compare: ", file1, file2
        #have to spawn a subprocess, because h5diff has no wrapper in python
        
        cl = "h5diff -cv '" + file1 + "' '" + file2 + "'"
        args = shlex.split(cl)
        print args
        '''
        cl_header1 = "h5dump --header " + file1
        args_header1 = shlex.split(cl_header1)
        cl_header2 = "h5dump --header " + file2
        args_header2 = shlex.split(cl_header2)
        try:
            p1 = Popen(args_header1, stdout=PIPE, stderr=PIPE)
            out1, err1 = p1.communicate()
            p2 = Popen(args_header2, stdout=PIPE, stderr=PIPE)
            out2, err2 = p2.communicate()
            if out1 != out2:
                print "different header dumps"
                print out1
                print ""
                print out2
        except Exception, e:
            print e
            return False
        #print args
        '''
        try:
            p = Popen(args, stdout=PIPE, stderr=PIPE)
            stdout, stderr = p.communicate()
            if p.returncode >0:
                print stdout
                print stderr
                return False
            else :
                return True
            
        except Exception, e:
            print e
            return False
        return True
