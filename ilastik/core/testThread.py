from PyQt4 import QtCore
import numpy
from ilastik.core import dataImpex

# this is the core replacement of the guiThread used to test module functionality
class TestThread(QtCore.QThread):
    
    def __init__(self, parent, baseMgr, listOfResultOverlays, listOfFilenames):
        __pyqtSignals__ = ( "done()")

        QtCore.QThread.__init__(self, parent)
        self.parent = parent
        self.baseMgr = baseMgr
        self.listOfResultOverlays = listOfResultOverlays
        self.listOfFilenames = listOfFilenames
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
        equalOverlays = True
        for i in range(len(self.listOfResultOverlays)):
            obtained = self.baseMgr.dataMgr[self.baseMgr.dataMgr._activeImageNumber].overlayMgr["Unsupervised/PCA component %d" % (i+1)]
            prefix = "Ground_Truth/"
            dataImpex.DataImpex.importOverlay(self.baseMgr.dataMgr[self.baseMgr.dataMgr._activeImageNumber], self.listOfFilenames[i], prefix)
            groundTruth = self.baseMgr.dataMgr[self.baseMgr.dataMgr._activeImageNumber].overlayMgr[prefix + "Unsupervised/PCA component %d" % (i+1)]
            equalOverlays = equalOverlays & self.compareOverlayData(obtained, groundTruth)
        print equalOverlays
        self.passedTest = equalOverlays
        self.emit(QtCore.SIGNAL("done()"))
        

        ## write out results
        #dataImpex.DataImpex.exportOverlay("unsupervised_PCA_component_1.h5", "h5", pca1)        
        #dataImpex.DataImpex.exportOverlay("unsupervised_PCA_component_2.h5", "h5", pca2)        
        #dataImpex.DataImpex.exportOverlay("unsupervised_PCA_component_3.h5", "h5", pca3)        

    def compareOverlayData(self, overlay1, overlay2):
        if numpy.all(overlay1._data._data - overlay2._data._data == 0):
            return True
        else: 
            return False
        