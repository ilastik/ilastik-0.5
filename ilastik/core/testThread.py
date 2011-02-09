from PyQt4 import QtCore
import numpy
from ilastik.core import dataImpex

# this is the core replacement of the guiThread used to test module functionality
class TestThread(QtCore.QObject):#QtCore.QThread):
    
    def __init__(self, baseMgr, listOfResultOverlays, listOfFilenames):
        __pyqtSignals__ = ( "done()")

        #QtCore.QThread.__init__(self, parent)
        QtCore.QObject.__init__(self)
        self.baseMgr = baseMgr
        self.listOfResultOverlays = listOfResultOverlays
        self.listOfFilenames = listOfFilenames
        self.passedTest = False

    def start(self, input):
        self.timer = QtCore.QTimer()
        QtCore.QObject.connect(self.timer, QtCore.SIGNAL("timeout()"), self.updateProgress)

        # call core function
        self.myTestThread = self.baseMgr.computeResults(input)
        self.timer.start(100)
        
    def updateProgress(self):
        if not self.myTestThread.isRunning():
            self.timer.stop()
            self.myTestThread.wait()
            self.finalize()

    def finalize(self):
        # call core function
        self.baseMgr.finalizeResults()
        # compare obtained results with ground truth results
        self.passedTest = TestHelperFuntions.compareResultsWithFile(self.baseMgr, self.listOfResultOverlays, self.listOfFilenames)
        # announce that we are done
        self.emit(QtCore.SIGNAL("done()"))
       

class TestHelperFuntions():
    @staticmethod
    def compareResultsWithFile(baseMgr, listOfResultOverlays, listOfFilenames):
        equalOverlays = True
        for i in range(len(listOfResultOverlays)):
            obtained = baseMgr.dataMgr[baseMgr.dataMgr._activeImageNumber].overlayMgr["Unsupervised/PCA component %d" % (i+1)]
            prefix = "Ground_Truth/"
            dataImpex.DataImpex.importOverlay(baseMgr.dataMgr[baseMgr.dataMgr._activeImageNumber], listOfFilenames[i], prefix)
            groundTruth = baseMgr.dataMgr[baseMgr.dataMgr._activeImageNumber].overlayMgr[prefix + "Unsupervised/PCA component %d" % (i+1)]
            equalOverlays = equalOverlays & TestHelperFuntions.compareOverlayData(obtained, groundTruth)
        return equalOverlays        
    
    @staticmethod
    def compareOverlayData(overlay1, overlay2):
        if numpy.all(overlay1._data._data - overlay2._data._data == 0):
            return True
        else: 
            return False
        