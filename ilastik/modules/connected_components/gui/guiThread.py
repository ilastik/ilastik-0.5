from ilastik.modules.connected_components.core import connectedComponentsMgr
from PyQt4 import QtGui, QtCore
from ilastik.core import overlayMgr
from ilastik.core.volume import DataAccessor

class CC(object):
    #Connected components
    
    def __init__(self, parent):
        self.parent = parent
        self.ilastik = parent
        #self.start()

    def start(self, backgroundClasses):
        self.parent.ribbon.getTab('Connected Components').btnCC.setEnabled(False)
        self.parent.ribbon.getTab('Connected Components').btnCCBack.setEnabled(False)
        self.timer = QtCore.QTimer()
        self.parent.connect(self.timer, QtCore.SIGNAL("timeout()"), self.updateProgress)
        overlay = self.parent.project.dataMgr[self.parent.project.dataMgr._activeImageNumber].Connected_Components.inputData
        if backgroundClasses is None:
            self.cc = connectedComponentsMgr.ConnectedComponentsThread(self.parent.project.dataMgr, overlay._data)
        else:
            self.cc = connectedComponentsMgr.ConnectedComponentsThread(self.parent.project.dataMgr, overlay._data, backgroundClasses)
        numberOfJobs = self.cc.numberOfJobs
        self.initCCProgress(numberOfJobs)
        self.cc.start()
        self.timer.start(200)
        
    def initCCProgress(self, numberOfJobs):
        statusBar = self.parent.statusBar()
        self.progressBar = QtGui.QProgressBar()
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(numberOfJobs)
        self.progressBar.setFormat(' Connected Components... %p%')
        statusBar.addWidget(self.progressBar)
        statusBar.show()

    def updateProgress(self):
        val = self.cc.count
        self.progressBar.setValue(val)
        if not self.cc.isRunning():
            print "finalizing connected components"
            self.timer.stop()
            self.cc.wait()
            self.finalize()
            self.terminateProgressBar()

    def finalize(self):

        #create Overlay for connected components:
        if self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["Connected Components/CC Results"] is None:
            #colortab = [QtGui.qRgb(i, i, i) for i in range(256)]
            colortab = self.makeColorTab()
            ov = overlayMgr.OverlayItem(self.parent._activeImage,self.cc.result, color = QtGui.QColor(255, 0, 0), alpha = 1.0, colorTable = colortab, autoAdd = True, autoVisible = True)
            self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["Connected Components/CC Results"] = ov
        else:
            self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["Connected Components/CC Results"]._data = DataAccessor(self.cc.result)
        self.ilastik.labelWidget.repaint()
       
    def terminateProgressBar(self):
        self.parent.statusBar().removeWidget(self.progressBar)
        self.parent.statusBar().hide()
        self.parent.ribbon.tabDict['Connected Components'].btnCC.setEnabled(True)
        self.parent.ribbon.tabDict['Connected Components'].btnCCBack.setEnabled(True)
    
    @staticmethod
    def makeColorTab():
        sublist = []
        #sublist.append(QtGui.qRgb(0, 0, 0))
        sublist.append(QtGui.qRgb(255, 255, 255))
        sublist.append(QtGui.qRgb(255, 0, 0))
        sublist.append(QtGui.qRgb(0, 255, 0))
        sublist.append(QtGui.qRgb(0, 0, 255))
        
        sublist.append(QtGui.qRgb(255, 255, 0))
        sublist.append(QtGui.qRgb(0, 255, 255))
        sublist.append(QtGui.qRgb(255, 0, 255))
        sublist.append(QtGui.qRgb(255, 105, 180)) #hot pink!
        
        sublist.append(QtGui.qRgb(102, 205, 170)) #dark aquamarine
        sublist.append(QtGui.qRgb(165,  42,  42)) #brown        
        sublist.append(QtGui.qRgb(0, 0, 128)) #navy
        sublist.append(QtGui.qRgb(255, 165, 0)) #orange
        
        sublist.append(QtGui.qRgb(173, 255,  47)) #green-yellow
        sublist.append(QtGui.qRgb(128,0, 128)) #purple
        sublist.append(QtGui.qRgb(192, 192, 192)) #silver
        sublist.append(QtGui.qRgb(240, 230, 140)) #khaki
        colorlist = []
        colorlist.append(long(0))
        for i in range(0, 16):
            colorlist.extend(sublist)
        colorlist.pop()
        return colorlist
        