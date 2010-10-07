import numpy
from PyQt4 import QtGui, QtCore
from ilastik.core.modules.Classification import classificationMgr
from ilastik.core import overlayMgr
from ilastik.core import activeLearning

class FeatureComputation(object):
    def __init__(self, parent):
        self.ilastik = self.parent = parent
        self.ilastik.lockRibbon(True)
        self.featureCompute()
    
    def featureCompute(self):
        self.parent.project.dataMgr.featureLock.acquire()
        self.myTimer = QtCore.QTimer()
        self.parent.connect(self.myTimer, QtCore.SIGNAL("timeout()"), self.updateFeatureProgress)
        self.parent.project.dataMgr.module["Classification"]["classificationMgr"].clearFeaturesAndTraining()
        numberOfJobs = self.parent.project.featureMgr.prepareCompute(self.parent.project.dataMgr)   
        self.initFeatureProgress(numberOfJobs)
        self.parent.project.featureMgr.triggerCompute()
        self.myTimer.start(200)
        
    def initFeatureProgress(self, numberOfJobs):
        statusBar = self.parent.statusBar()
        self.myFeatureProgressBar = QtGui.QProgressBar()
        self.myFeatureProgressBar.setMinimum(0)
        self.myFeatureProgressBar.setMaximum(numberOfJobs)
        self.myFeatureProgressBar.setFormat(' Features... %p%')
        statusBar.addWidget(self.myFeatureProgressBar)
        statusBar.show()
    
    def updateFeatureProgress(self):
        val = self.parent.project.featureMgr.getCount() 
        self.myFeatureProgressBar.setValue(val)
        if not self.parent.project.featureMgr.featureProcess.isRunning():
            self.myTimer.stop()
            self.terminateFeatureProgressBar()
            self.parent.project.featureMgr.joinCompute(self.parent.project.dataMgr)   
            self.parent.project.createFeatureOverlays()

            
    def terminateFeatureProgressBar(self):
        self.parent.statusBar().removeWidget(self.myFeatureProgressBar)
        self.parent.statusBar().hide()
        self.parent.project.dataMgr.module["Classification"]["classificationMgr"].buildTrainingMatrix()
        self.parent.project.dataMgr.featureLock.release()
        if hasattr(self.parent, "classificationInteractive"):
            self.parent.classificationInteractive.updateThreadQueues()
            
        self.parent.ribbon.getTab('Classification').btnSelectFeatures.setEnabled(True)
        self.parent.ribbon.getTab('Classification').btnTrainPredict.setEnabled(True)
        self.parent.ribbon.getTab('Classification').btnStartLive.setEnabled(True)
        self.ilastik.lockRibbon(False)
                  
    def featureShow(self, item):
        pass

class ClassificationTrain(QtCore.QObject):
    def __init__(self, parent):
        QtCore.QObject.__init__(self)
        self.parent = parent
        self.ilastik = parent
        self.start()
        
    def start(self):
        #process all unaccounted label changes
        self.ilastik.lockRibbon(True)
        self.parent.ribbon.getTab('Classification').btnTrainPredict.setEnabled(False)
        self.parent.ribbon.getTab('Automate').btnBatchProcess.setEnabled(False)
        
        newLabels = self.parent.volumeEditor.getPendingLabels()
        if len(newLabels) > 0:
            self.parent.project.dataMgr.updateTrainingMatrix(newLabels)
        
        self.classificationTimer = QtCore.QTimer()
        self.parent.connect(self.classificationTimer, QtCore.SIGNAL("timeout()"), self.updateClassificationProgress)      
        numberOfJobs = 10                 
        self.initClassificationProgress(numberOfJobs)
        
        self.classificationProcess = classificationMgr.ClassifierTrainThread(numberOfJobs, self.parent.project.dataMgr, classifier = self.parent.project.classifier)
        self.classificationProcess.start()
        self.classificationTimer.start(500) 

    def initClassificationProgress(self, numberOfJobs):
        statusBar = self.parent.statusBar()
        self.myClassificationProgressBar = QtGui.QProgressBar()
        self.myClassificationProgressBar.setMinimum(0)
        self.myClassificationProgressBar.setMaximum(numberOfJobs)
        self.myClassificationProgressBar.setFormat(' Training... %p%')
        statusBar.addWidget(self.myClassificationProgressBar)
        statusBar.show()
    
    def updateClassificationProgress(self):
        val = self.classificationProcess.count
        self.myClassificationProgressBar.setValue(val)
        if not self.classificationProcess.isRunning():
            self.finalize()
            
    def finalize(self):
        self.classificationTimer.stop()
        self.classificationProcess.wait()
        self.terminateClassificationProgressBar()
        self.emit(QtCore.SIGNAL("trainingFinished()"))
        self.ilastik.lockRibbon(True)
                      
    def terminateClassificationProgressBar(self):
        self.parent.statusBar().removeWidget(self.myClassificationProgressBar)
        self.parent.statusBar().hide()

        self.parent.ribbon.getTab('Classification').btnTrainPredict.setEnabled(True)
        self.parent.ribbon.getTab('Automate').btnBatchProcess.setEnabled(True)
        

class ClassificationInteractive(object):
    def __init__(self, parent):
        
        self.ilastik = self.parent = parent
        self.stopped = False
        
        self.parent.ribbon.getTab('Classification').btnTrainPredict.setEnabled(False)
        self.parent.ribbon.getTab('Automate').btnBatchProcess.setEnabled(False)
        
        self.parent.volumeEditor.connect(self.parent.volumeEditor, QtCore.SIGNAL('newLabelsPending()'), self.updateThreadQueues)

        self.parent.volumeEditor.connect(self.parent.volumeEditor, QtCore.SIGNAL('changedSlice(int, int)'), self.updateThreadQueues)

        self.temp_cnt = 0
        
        descriptions =  self.parent.project.dataMgr.module["Classification"]["labelDescriptions"]
        activeImage = self.parent._activeImage
        
        for p_num,pd in enumerate(descriptions):
            #create Overlay for _prediction if not there:
            if activeImage.overlayMgr["Classification/Prediction/" + descriptions[p_num-1].name] is None:
                data = numpy.zeros(activeImage.shape, 'uint8')
                ov = overlayMgr.OverlayItem(data,  color = QtGui.QColor.fromRgba(long(descriptions[p_num-1].color)), alpha = 0.4, colorTable = None, autoAdd = True, autoVisible = True)
                activeImage.overlayMgr["Classification/Prediction/" + descriptions[p_num-1].name] = ov

        #create Overlay for uncertainty:
        if activeImage.overlayMgr["Classification/Uncertainty"] is None:
            data = numpy.zeros(activeImage.shape, 'uint8')
            ov = overlayMgr.OverlayItem(data, color = QtGui.QColor(255, 0, 0), alpha = 1.0, colorTable = None, autoAdd = True, autoVisible = False)
            activeImage.overlayMgr["Classification/Uncertainty"] = ov
        
        self.start()
    
    def updateThreadQueues(self, a = 0, b = 0):
        if self.classificationInteractive is not None:
            self.myInteractionProgressBar.setVisible(True)
            self.classificationInteractive.dataPending.set()

    def updateLabelWidget(self):
        try:
            self.myInteractionProgressBar.setVisible(False)
            self.parent.volumeEditor.repaint()                    
        except IndexError:
            pass
                


    def initInteractiveProgressBar(self):
        statusBar = self.parent.statusBar()
        self.myInteractionProgressBar = QtGui.QProgressBar()
        self.myInteractionProgressBar.setVisible(False)
        self.myInteractionProgressBar.setMinimum(0)
        self.myInteractionProgressBar.setMaximum(0)
        statusBar.addWidget(self.myInteractionProgressBar)
        statusBar.show()
        
    def terminateClassificationProgressBar(self):
        self.parent.statusBar().removeWidget(self.myInteractionProgressBar)
        self.parent.statusBar().hide()
        
    def start(self):
        self.ilastik.lockRibbon(True)
        self.initInteractiveProgressBar()
        self.classificationInteractive = classificationMgr.ClassifierInteractiveThread(self.parent, self.parent.project.dataMgr.module["Classification"]["classificationMgr"],classifier = self.parent.project.classifier)

        self.parent.connect(self.classificationInteractive, QtCore.SIGNAL("resultsPending()"), self.updateLabelWidget)      
    
               
        self.classificationInteractive.start()
        self.updateThreadQueues()
        
        
    def stop(self):
        self.classificationInteractive.stopped = True

        self.classificationInteractive.dataPending.set() #wake up thread one last time before his death
        self.classificationInteractive.wait()
        self.finalize()
        
        self.terminateClassificationProgressBar()
        self.ilastik.ribbonBusy = False
    
    def finalize(self):
        self.parent.ribbon.getTab('Classification').btnTrainPredict.setEnabled(True)
        self.parent.ribbon.getTab('Automate').btnBatchProcess.setEnabled(True)
        self.parent.project.dataMgr.Classification.classificationMgr.classifiers = list(self.classificationInteractive.classifiers)
        self.ilastik.lockRibbon(False)
        

class ClassificationPredict(object):
    def __init__(self, parent):
        self.ilastik = self.parent = parent
        self.start()
    
    def start(self):
        self.ilastik.lockRibbon(True)
        self.parent.ribbon.getTab('Classification').btnTrainPredict.setEnabled(False)
        self.parent.ribbon.getTab('Classification').btnStartLive.setEnabled(False)
         
        self.classificationTimer = QtCore.QTimer()
        self.parent.connect(self.classificationTimer, QtCore.SIGNAL("timeout()"), self.updateClassificationProgress)      
                    
        self.classificationPredict = classificationMgr.ClassifierPredictThread(self.parent.project.dataMgr)
        numberOfJobs = self.classificationPredict.numberOfJobs
        self.initClassificationProgress(numberOfJobs)
        self.classificationPredict.start()
        self.classificationTimer.start(200)

    def initClassificationProgress(self, numberOfJobs):
        statusBar = self.parent.statusBar()
        self.myClassificationProgressBar = QtGui.QProgressBar()
        self.myClassificationProgressBar.setMinimum(0)
        self.myClassificationProgressBar.setMaximum(numberOfJobs)
        self.myClassificationProgressBar.setFormat(' Prediction... %p%')
        statusBar.addWidget(self.myClassificationProgressBar)
        statusBar.show()
    
    def updateClassificationProgress(self):
        val = self.classificationPredict.count
        self.myClassificationProgressBar.setValue(val)
        if not self.classificationPredict.isRunning():
            self.classificationTimer.stop()

            self.classificationPredict.wait()
            self.finalize()           
            self.terminateClassificationProgressBar()

    def finalize(self):
        activeImage = self.parent._activeImage
        self.classificationPredict.generateOverlays(activeImage)
        self.parent.volumeEditor.repaint()
        self.ilastik.lockRibbon(False)
        
    def terminateClassificationProgressBar(self):
        self.parent.statusBar().removeWidget(self.myClassificationProgressBar)
        self.parent.statusBar().hide()
        self.parent.ribbon.getTab('Classification').btnTrainPredict.setEnabled(True)
        self.parent.ribbon.getTab('Classification').btnStartLive.setEnabled(True)
        self.parent.ribbon.getTab('Classification').btnExportClassifier.setEnabled(True)
