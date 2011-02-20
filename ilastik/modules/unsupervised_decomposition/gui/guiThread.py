from PyQt4 import QtGui, QtCore

#*******************************************************************************
# U n s u p e r v i s e d D e c o m p o s i t i o n                            *
#*******************************************************************************

class UnsupervisedDecomposition(object):
    
    def __init__(self, parent):
        self.parent = parent
        self.ilastik = parent

    def start(self, overlays):
        self.parent.ribbon.getTab('Unsupervised Decomposition').btnDecompose.setEnabled(False)
        
        self.timer = QtCore.QTimer()
        self.parent.connect(self.timer, QtCore.SIGNAL("timeout()"), self.updateProgressBar)

        # call core function
        self.ud = self.parent.project.dataMgr.Unsupervised_Decomposition.computeResults(overlays)

        # create and handle progress bar
        self.timer.start(200)
        #numberOfJobs = self.ud.numberOfJobs         USE IF YOU WANT TO UPDATE THE PROGRESS BAR WITH A PERCENTAGE
        self.initProgressBar()                     # USE (numberOfJobs) IF YOU WANT TO UPDATE THE PROGRESS BAR WITH A PERCENTAGE
        
    def initProgressBar(self):#, numberOfJobs):    # USE (.., numberOfJobs) IF YOU WANT TO UPDATE THE PROGRESS BAR WITH A PERCENTAGE
        statusBar = self.parent.statusBar()
        self.progressBar = QtGui.QProgressBar()
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(0)             # USE (numberOfJobs) IF YOU WANT TO UPDATE THE PROGRESS BAR WITH A PERCENTAGE
        self.progressBar.setValue(0)
        self.progressBar.setFormat(' Unsupervised Decomposition... %p%')
        statusBar.addWidget(self.progressBar)
        statusBar.show()

    def updateProgressBar(self):
        #val = self.ud.count                USE IF YOU WANT TO UPDATE THE PROGRESS BAR WITH A PERCENTAGE
        #self.progressBar.setValue(val)     USE IF YOU WANT TO UPDATE THE PROGRESS BAR WITH A PERCENTAGE
        if not self.ud.isRunning():
            self.timer.stop()
            self.ud.wait()
            self.finalize()
            self.terminateProgressBar()

    def finalize(self):
        self.parent.project.dataMgr.Unsupervised_Decomposition.finalizeResults()
        self.ilastik.labelWidget.repaint()

    def terminateProgressBar(self):
        self.parent.statusBar().removeWidget(self.progressBar)
        self.parent.statusBar().hide()
        self.parent.ribbon.getTab('Unsupervised Decomposition').btnDecompose.setEnabled(True)

