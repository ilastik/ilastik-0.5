from PyQt4 import QtGui, QtCore

class CC(object):
    #Connected components

    def __init__(self, parent):
        #A list of labels which denote 'background'
        #The corresponding connected components will not be displayed in 3D
        self.backgroundClasses = set()
        
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
        
        #Update overlay with information on how to display it in 3D (if possible)
        ov = self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["Connected Components/CC Results"]
        if len(self.backgroundClasses) > 0:
            ov.displayable3D = True
            ov.backgroundClasses = set([0])
        
        self.ilastik.labelWidget.repaint()
       
    def terminateProgressBar(self):
        self.parent.statusBar().removeWidget(self.progressBar)
        self.parent.statusBar().hide()
        self.parent.ribbon.tabDict['Connected Components'].btnCC.setEnabled(True)
        self.parent.ribbon.tabDict['Connected Components'].btnCCBack.setEnabled(True)
    
