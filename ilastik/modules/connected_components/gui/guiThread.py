from PyQt4 import QtGui, QtCore

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

        # call core function
        self.cc = self.parent.project.dataMgr.Connected_Components.computeResults(backgroundClasses)

        self.timer.start(200)
        self.initCCProgress()
        
    def initCCProgress(self):
        statusBar = self.parent.statusBar()
        self.progressBar = QtGui.QProgressBar()
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(0)
        self.progressBar.setValue(1)

        self.progressBar.setFormat(' Connected Components... %p%')
        statusBar.addWidget(self.progressBar)
        statusBar.show()

    def updateProgress(self):
        if not self.cc.isRunning():
            print "finalizing connected components"
            self.timer.stop()
            self.cc.wait()
            self.finalize()
            self.terminateProgressBar()

    def finalize(self):
        self.parent.project.dataMgr.Connected_Components.finalizeResults()            
        self.ilastik.labelWidget.repaint()
       
    def terminateProgressBar(self):
        self.parent.statusBar().removeWidget(self.progressBar)
        self.parent.statusBar().hide()
        self.parent.ribbon.tabDict['Connected Components'].btnCC.setEnabled(True)
        self.parent.ribbon.tabDict['Connected Components'].btnCCBack.setEnabled(True)
    
    @classmethod
    def makeColorTab(cls):
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
        