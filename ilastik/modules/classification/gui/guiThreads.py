#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    Copyright 2010, 2011 C Sommer, C Straehle, U Koethe, FA Hamprecht. All rights reserved.
#    
#    Redistribution and use in source and binary forms, with or without modification, are
#    permitted provided that the following conditions are met:
#    
#       1. Redistributions of source code must retain the above copyright notice, this list of
#          conditions and the following disclaimer.
#    
#       2. Redistributions in binary form must reproduce the above copyright notice, this list
#          of conditions and the following disclaimer in the documentation and/or other materials
#          provided with the distribution.
#    
#    THIS SOFTWARE IS PROVIDED BY THE ABOVE COPYRIGHT HOLDERS ``AS IS'' AND ANY EXPRESS OR IMPLIED
#    WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
#    FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE ABOVE COPYRIGHT HOLDERS OR
#    CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#    CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#    SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
#    ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#    NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
#    ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#    
#    The views and conclusions contained in the software and documentation are those of the
#    authors and should not be interpreted as representing official policies, either expressed
#    or implied, of their employers.

from PyQt4.QtCore import QObject, QTimer, SIGNAL
from PyQt4.QtGui import QColor, QErrorMessage, QProgressBar

import numpy
from ilastik.modules.classification.core import classificationMgr
from ilastik.core import overlayMgr
import ilastik.core.overlays.thresholdOverlay as tho

#*******************************************************************************
# F e a t u r e C o m p u t a t i o n                                          *
#*******************************************************************************

class FeatureComputation(QObject):
    def __init__(self, parent):
        QObject.__init__(self)
        self.ilastik = self.parent = parent
        self.featureCompute() 
    
    def featureCompute(self):
        self.parent.setTabBusy(True)
        self.parent.ribbon.getTab('Classification').btnClassifierOptions.setEnabled(False)
        self.parent.ribbon.getTab('Classification').btnSelectFeatures.setEnabled(False)        
        self.parent.project.dataMgr.featureLock.acquire()
        self.myTimer = QTimer(self)
        self.parent.connect(self.myTimer, SIGNAL("timeout()"), self.updateFeatureProgress)
        self.parent.project.dataMgr.module["Classification"]["classificationMgr"].clearFeaturesAndTraining()
        numberOfJobs = self.ilastik.project.dataMgr.Classification.featureMgr.prepareCompute(self.parent.project.dataMgr)   
        self.initFeatureProgress(numberOfJobs)
        self.ilastik.project.dataMgr.Classification.featureMgr.triggerCompute()
        self.myTimer.start(200)
        
    def initFeatureProgress(self, numberOfJobs):
        statusBar = self.parent.statusBar()
        self.myFeatureProgressBar = QProgressBar()
        self.myFeatureProgressBar.setMinimum(0)
        self.myFeatureProgressBar.setMaximum(numberOfJobs)
        self.myFeatureProgressBar.setFormat(' Features... %p%')
        statusBar.addWidget(self.myFeatureProgressBar)
        statusBar.show()
    
    def updateFeatureProgress(self):
        val = self.ilastik.project.dataMgr.Classification.featureMgr.getCount() 
        self.myFeatureProgressBar.setValue(val)
        if not self.ilastik.project.dataMgr.Classification.featureMgr.featureProcess.isRunning():
            self.terminateFeatureProgressBar()
            self.ilastik.project.dataMgr.Classification.featureMgr.joinCompute(self.parent.project.dataMgr)   

            
    def terminateFeatureProgressBar(self):
        self.myTimer.stop()
        del self.myTimer
        
        self.parent.statusBar().removeWidget(self.myFeatureProgressBar)
        self.parent.statusBar().hide()
        self.parent.project.dataMgr.module["Classification"]["classificationMgr"].buildTrainingMatrix()
        self.parent.project.dataMgr.featureLock.release()
        if hasattr(self.parent, "classificationInteractive"):
            self.parent.classificationInteractive.updateThreadQueues()
            
        self.parent.ribbon.getTab('Classification').btnSelectFeatures.setEnabled(True)
        self.parent.ribbon.getTab('Classification').btnTrainPredict.setEnabled(True)
        self.parent.ribbon.getTab('Classification').btnStartLive.setEnabled(True)
        self.parent.ribbon.getTab('Classification').btnClassifierOptions.setEnabled(True)
        self.parent.ribbon.getTab('Classification').btnSelectFeatures.setEnabled(True)        
        self.parent.setTabBusy(False)
                    
    def featureShow(self, item):
        pass

#*******************************************************************************
# C l a s s i f i c a t i o n T r a i n                                        *
#*******************************************************************************

class ClassificationTrain(QObject):
    def __init__(self, parent):
        QObject.__init__(self)
        self.parent = parent
        self.ilastik = parent
        self.start()
        
    def start(self):
        self.parent.setTabBusy(True)
        #process all unaccounted label changes
        self.parent.ribbon.getTab('Classification').btnTrainPredict.setEnabled(False)
        self.parent.ribbon.getTab('Automate').btnBatchProcess.setEnabled(False)
        self.parent.ribbon.getTab('Classification').btnClassifierOptions.setEnabled(False)
        self.parent.ribbon.getTab('Classification').btnSelectFeatures.setEnabled(False)
        
        newLabels = self.parent.labelWidget.getPendingLabels()
        if len(newLabels) > 0:
            self.parent.project.dataMgr.Classification.classificationMgr.updateTrainingMatrix(newLabels)
        
        self.classificationTimer = QTimer(self)
        self.parent.connect(self.classificationTimer, SIGNAL("timeout()"), self.updateClassificationProgress)      
        numberOfJobs = 10                 
        self.initClassificationProgress(numberOfJobs)
        
        self.classificationProcess = classificationMgr.ClassifierTrainThread(numberOfJobs, self.parent.project.dataMgr, classifier = self.parent.project.dataMgr.module["Classification"].classifier)
        self.classificationProcess.start()
        self.classificationTimer.start(500) 

    def initClassificationProgress(self, numberOfJobs):
        statusBar = self.parent.statusBar()
        self.myClassificationProgressBar = QProgressBar()
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
        del self.classificationTimer
        self.classificationProcess.wait()
        self.terminateClassificationProgressBar()
        self.parent.setTabBusy(False)
        self.emit(SIGNAL("trainingFinished()"))
                      
    def terminateClassificationProgressBar(self):
        self.parent.statusBar().removeWidget(self.myClassificationProgressBar)
        self.parent.statusBar().hide()

        self.parent.ribbon.getTab('Classification').btnTrainPredict.setEnabled(True)
        self.parent.ribbon.getTab('Automate').btnBatchProcess.setEnabled(True)
        self.parent.ribbon.getTab('Classification').btnClassifierOptions.setEnabled(True)
        self.parent.ribbon.getTab('Classification').btnSelectFeatures.setEnabled(True)
        

#*******************************************************************************
# C l a s s i f i c a t i o n I n t e r a c t i v e                            *
#*******************************************************************************

class ClassificationInteractive(object):
    def __init__(self, parent):
        self.parent = parent
        self.stopped = False
        
        self.parent.ribbon.getTab('Classification').btnTrainPredict.setEnabled(False)
        self.parent.ribbon.getTab('Automate').btnBatchProcess.setEnabled(False)

        self.parent.ribbon.getTab('Classification').btnTrainPredict.setEnabled(False)
        self.parent.ribbon.getTab('Classification').btnClassifierOptions.setEnabled(False)
        self.parent.ribbon.getTab('Classification').btnSelectFeatures.setEnabled(False)
                
        self.parent.labelWidget.connect(self.parent.labelWidget, SIGNAL('newLabelsPending()'), self.updateThreadQueues)

        self.parent.labelWidget.connect(self.parent.labelWidget, SIGNAL('changedSlice(int, int)'), self.updateThreadQueues)

        self.temp_cnt = 0
        
        descriptions =  self.parent.project.dataMgr.module["Classification"]["labelDescriptions"]
        activeImage = self.parent._activeImage
        
        
        foregrounds = []
        
        for p_num,pd in enumerate(descriptions):
            #create Overlay for _prediction if not there:
            if activeImage.overlayMgr["Classification/Prediction/" + descriptions[p_num-1].name] is None:
                data = numpy.zeros(activeImage.shape[0:-1] + (1,), 'float32')
                ov = overlayMgr.OverlayItem(data,  color = QColor.fromRgba(long(descriptions[p_num-1].color)), alpha = 0.4, colorTable = None, autoAdd = True, autoVisible = True, min = 0, max = 1.0)
                ov.setColorGetter(descriptions[p_num-1].getColor, descriptions[p_num-1])
                activeImage.overlayMgr["Classification/Prediction/" + descriptions[p_num-1].name] = ov
            ov = activeImage.overlayMgr["Classification/Prediction/" + descriptions[p_num-1].name]
            foregrounds.append(ov)
                

        #create Overlay for uncertainty:
        if activeImage.overlayMgr["Classification/Uncertainty"] is None:
            data = numpy.zeros(activeImage.shape[0:-1] + (1,), 'float32')
            ov = overlayMgr.OverlayItem(data, color = QColor(255, 0, 0), alpha = 1.0, colorTable = None, autoAdd = True, autoVisible = False, min = 0, max = 1)
            activeImage.overlayMgr["Classification/Uncertainty"] = ov

        if len(foregrounds) > 1:
            if activeImage.overlayMgr["Classification/Segmentation"] is None:
                ov = tho.ThresholdOverlay(foregrounds, [], autoAdd = True, autoVisible = False)
                activeImage.overlayMgr["Classification/Segmentation"] = ov
            else:
                ov = activeImage.overlayMgr["Classification/Segmentation"]
                ov.setForegrounds(foregrounds)
        
        self.start()
    
    def updateThreadQueues(self, a = 0, b = 0):
        if self.classificationInteractive is not None:
            self.myInteractionProgressBar.setVisible(True)
            self.classificationInteractive.dataPending.set()

    def updateLabelWidget(self):
        try:
            self.myInteractionProgressBar.setVisible(False)
            self.parent.labelWidget.repaint()                    
        except IndexError:
            pass
                


    def initInteractiveProgressBar(self):
        statusBar = self.parent.statusBar()
        self.myInteractionProgressBar = QProgressBar()
        self.myInteractionProgressBar.setVisible(False)
        self.myInteractionProgressBar.setMinimum(0)
        self.myInteractionProgressBar.setMaximum(0)
        statusBar.addWidget(self.myInteractionProgressBar)
        statusBar.show()
        
    def terminateClassificationProgressBar(self):
        self.parent.statusBar().removeWidget(self.myInteractionProgressBar)
        self.parent.statusBar().hide()
        
    def start(self):
        self.parent.setTabBusy(True)
        self.initInteractiveProgressBar()
        self.classificationInteractive = classificationMgr.ClassifierInteractiveThread(self.parent, self.parent.project.dataMgr.module["Classification"]["classificationMgr"],classifier = self.parent.project.dataMgr.module["Classification"].classifier)

        self.parent.connect(self.classificationInteractive, SIGNAL("resultsPending()"), self.updateLabelWidget)      
    
               
        self.classificationInteractive.start()
        self.updateThreadQueues()
        
        
    def stop(self):
        self.classificationInteractive.stopped = True
        
        self.classificationInteractive.dataPending.set() #wake up thread one last time before his death
        
        self.classificationInteractive.wait()
        self.finalize()

        self.parent.ribbon.getTab('Classification').btnTrainPredict.setEnabled(True)
        self.parent.ribbon.getTab('Classification').btnClassifierOptions.setEnabled(True)
        self.parent.ribbon.getTab('Classification').btnSelectFeatures.setEnabled(True)
        
        self.terminateClassificationProgressBar()
        self.parent.setTabBusy(False)
    
    def finalize(self):
        self.parent.ribbon.getTab('Classification').btnTrainPredict.setEnabled(True)
        self.parent.ribbon.getTab('Automate').btnBatchProcess.setEnabled(True)
        self.parent.project.dataMgr.Classification.classificationMgr.classifiers = list(self.classificationInteractive.classifiers)
        self.classificationInteractive =  None
        

#*******************************************************************************
# C l a s s i f i c a t i o n P r e d i c t                                    *
#*******************************************************************************

class ClassificationPredict(QObject):
    def __init__(self, parent):
        QObject.__init__(self)
        self.parent = parent
        self.start()
    
    def start(self):
        self.parent.setTabBusy(True)       
        self.parent.ribbon.getTab('Classification').btnTrainPredict.setEnabled(False)
        self.parent.ribbon.getTab('Classification').btnStartLive.setEnabled(False)
        self.parent.ribbon.getTab('Classification').btnClassifierOptions.setEnabled(False)
        self.parent.ribbon.getTab('Classification').btnSelectFeatures.setEnabled(False)
        
        
        self.classificationTimer = QTimer(self)
        self.parent.connect(self.classificationTimer, SIGNAL("timeout()"), self.updateClassificationProgress)      
                    
        self.classificationPredict = classificationMgr.ClassifierPredictThread(self.parent.project.dataMgr)
        numberOfJobs = self.classificationPredict.numberOfJobs
        self.initClassificationProgress(numberOfJobs)
        self.classificationPredict.start()
        self.classificationTimer.start(200)

    def initClassificationProgress(self, numberOfJobs):
        statusBar = self.parent.statusBar()
        self.myClassificationProgressBar = QProgressBar()
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
        self.classificationTimer.stop()
        del self.classificationTimer 
        try:
            self.classificationPredict.generateOverlays(self.parent._activeImage)
            self.parent.labelWidget.repaint()
        except MemoryError,e:
            print "Out of memory:", e
            QErrorMessage.qtHandler().showMessage("Not enough memory to create all classification results")
        self.parent.setTabBusy(False)
        
    def terminateClassificationProgressBar(self):
        self.parent.statusBar().removeWidget(self.myClassificationProgressBar)
        self.parent.statusBar().hide()
        self.parent.ribbon.getTab('Classification').btnTrainPredict.setEnabled(True)
        self.parent.ribbon.getTab('Classification').btnStartLive.setEnabled(True)
        self.parent.ribbon.getTab('Classification').btnExportClassifier.setEnabled(True)
        self.parent.ribbon.getTab('Classification').btnClassifierOptions.setEnabled(True)
        self.parent.ribbon.getTab('Classification').btnSelectFeatures.setEnabled(True)
