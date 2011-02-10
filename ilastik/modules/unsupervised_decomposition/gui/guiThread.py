from ilastik.modules.unsupervised_decomposition.core import unsupervisedMgr
from PyQt4 import QtGui, QtCore
from ilastik.core import overlayMgr
from ilastik.core.overlayMgr import OverlayItem
import numpy
from ilastik.core.volume import DataAccessor

class UnsupervisedDecomposition(object):
    
    def __init__(self, parent):
        self.parent = parent
        self.ilastik = parent

    def start(self, overlays):
        self.parent.ribbon.getTab('Unsupervised Decomposition').btnDecompose.setEnabled(False)
        
        self.timer = QtCore.QTimer()
        self.parent.connect(self.timer, QtCore.SIGNAL("timeout()"), self.updateProgress)

        #self.ud = unsupervisedMgr.UnsupervisedDecompositionThread(self.parent.project.dataMgr, overlays, self.parent.project.unsupervisedDecomposer)
        self.ud = unsupervisedMgr.UnsupervisedDecompositionThread(self.parent.project.dataMgr, overlays, self.parent.project.dataMgr.module["Unsupervised_Decomposition"].unsupervisedMethod)

        numberOfJobs = self.ud.numberOfJobs
        self.initDecompositionProgress(numberOfJobs)
        self.ud.start()
        self.timer.start(200)
        
    def initDecompositionProgress(self, numberOfJobs):
        statusBar = self.parent.statusBar()
        self.progressBar = QtGui.QProgressBar()
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(0)
        self.progressBar.setValue(0)
        self.progressBar.setFormat(' Unsupervised Decomposition... %p%')
        statusBar.addWidget(self.progressBar)
        statusBar.show()

    def updateProgress(self):
        val = self.ud.count
        self.progressBar.setValue(val)
        if not self.ud.isRunning():
            self.timer.stop()
            self.ud.wait()
            self.finalize()
            self.terminateProgressBar()

    def finalize(self):
        activeItem = self.parent.project.dataMgr[self.parent._activeImageNumber]
        activeItem._dataVol.unsupervised = self.ud.result

        #create Overlay for unsupervised decomposition:
        if self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["Unsupervised/pLSA"] is None:
            data = self.ud.result[:,:,:,:,:]
            colortab = [QtGui.qRgb(i, i, i) for i in range(256)]
            for o in range(0, data.shape[4]):
                # transform to uint8
                data2 = data[:,:,:,:,o:(o+1)]
                dmin = numpy.min(data2)
                data2 -= dmin
                dmax = numpy.max(data2)
                data2 = 255/dmax*data2
                data2 = data2.astype(numpy.uint8)
                
                ov = OverlayItem(data2, color = QtGui.QColor(255, 0, 0), alpha = 1.0, colorTable = colortab, autoAdd = True, autoVisible = True)
                self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["Unsupervised/" + self.parent.project.dataMgr.module["Unsupervised_Decomposition"].unsupervisedMethod.shortname + " component %d" % (o+1)] = ov
        else:
            self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["Unsupervised/" + self.parent.project.dataMgr.module["Unsupervised_Decomposition"].unsupervisedMethod.shortname]._data = DataAccessor(self.ud.result)
        self.ilastik.labelWidget.repaint()

    def terminateProgressBar(self):
        self.parent.statusBar().removeWidget(self.progressBar)
        self.parent.statusBar().hide()
        self.parent.ribbon.getTab('Unsupervised Decomposition').btnDecompose.setEnabled(True)

