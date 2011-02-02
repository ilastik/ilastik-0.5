from ilastik.core.baseModuleMgr import BaseModuleDataItemMgr, BaseModuleMgr

import numpy
import traceback, sys
import threading
from ilastik.core.overlayMgr import OverlayItem
from ilastik.core import jobMachine
from PyQt4 import QtGui, QtCore
import os
import algorithms
from ilastik.core.volume import DataAccessor
#from algorithms.unsupervisedDecompositionBase import UnsupervisedDecompositionBase
#from algorithms.unsupervisedDecompositionPCA import UnsupervisedDecompositionPCA
#from algorithms.unsupervisedDecompositionPLSA import UnsupervisedDecompositionPLSA

""" Import all algorithm plugins"""
pathext = os.path.dirname(__file__)

try:
    for f in os.listdir(os.path.abspath(pathext + '/algorithms')):
        module_name, ext = os.path.splitext(f) # Handles no-extension files, etc.
        if ext == '.py': # Important, ignore .pyc/othesr files.
            module = __import__('ilastik.modules.unsupervised_decomposition.core.algorithms.' + module_name)
except Exception, e:
    print e
    traceback.print_exc()
    pass

for i, c in enumerate(algorithms.unsupervisedDecompositionBase.UnsupervisedDecompositionBase.__subclasses__()):
    print "Loaded unsupervised decomposition algorithm:", c.name


def interactiveMessagePrint(* args):
    pass
    #print "Thread: ", args[0]


class UnsupervisedItemModuleMgr(BaseModuleDataItemMgr):
    name = "Unsupervised_Decomposition"
    
    def __init__(self, dataItemImage):
        BaseModuleDataItemMgr.__init__(self, dataItemImage)
        self.dataItemImage = dataItemImage
        self.overlays = []
        self.inputData = None
        
    def setInputData(self, data):
        self.inputData = data
        
class UnsupervisedDecompositionModuleMgr(BaseModuleMgr):
    name = "Unsupervised_Decomposition"
         
    def __init__(self, dataMgr):
        BaseModuleMgr.__init__(self, dataMgr)
        self.dataMgr = dataMgr
        self.unsupervisedMethod = algorithms.unsupervisedDecompositionPCA.UnsupervisedDecompositionPCA
        if self.dataMgr.module["Unsupervised_Decomposition"] is None:
            self.dataMgr.module["Unsupervised_Decomposition"] = self

    def computeResults(self, inputOverlays):
        self.ud = UnsupervisedDecompositionThread(self.dataMgr, inputOverlays, self.dataMgr.module["Unsupervised_Decomposition"].unsupervisedMethod)
        self.ud.start()
        return self.ud
    
    def finalizeResults(self):
        activeItem = self.dataMgr[self.dataMgr._activeImageNumber]
        activeItem._dataVol.unsupervised = self.ud.result

        #create overlays for unsupervised decomposition:
        if self.dataMgr[self.dataMgr._activeImageNumber].overlayMgr["Unsupervised/" + self.dataMgr.module["Unsupervised_Decomposition"].unsupervisedMethod.shortname] is None:
            data = self.ud.result[:,:,:,:,:]
            colorTab = [QtGui.qRgb(i, i, i) for i in range(256)]
            currColor = QtGui.QColor(255, 0, 0)
            for o in range(0, data.shape[4]):
                # transform to uint8
                data2 = data[:,:,:,:,o:(o+1)]
                dmin = numpy.min(data2)
                data2 -= dmin
                dmax = numpy.max(data2)
                data2 = 255/dmax*data2
                data2 = data2.astype(numpy.uint8)
                
                ov = OverlayItem(data2, color = currColor, alpha = 1.0, colorTable = colorTab, autoAdd = True, autoVisible = True)
                self.dataMgr[self.dataMgr._activeImageNumber].overlayMgr["Unsupervised/" + self.dataMgr.module["Unsupervised_Decomposition"].unsupervisedMethod.shortname + " component %d" % (o+1)] = ov
        else:
            self.dataMgr[self.dataMgr._activeImageNumber].overlayMgr["Unsupervised/" + self.dataMgr.module["Unsupervised_Decomposition"].unsupervisedMethod.shortname]._data = DataAccessor(self.ud.result)
            
class UnsupervisedDecompositionThread(QtCore.QThread):
    def __init__(self, dataMgr, overlays, unsupervisedMethod = algorithms.unsupervisedDecompositionPCA.UnsupervisedDecompositionPCA, unsupervisedMethodOptions = None):
        QtCore.QThread.__init__(self, None)
        self.reshapeToFeatures(overlays)
        self.dataMgr = dataMgr
        self.count = 0
        self.numberOfJobs = 1
        self.stopped = False
        self.unsupervisedMethod = unsupervisedMethod
        self.unsupervisedMethodOptions = unsupervisedMethodOptions
        self.jobMachine = jobMachine.JobMachine()

    def reshapeToFeatures(self, overlays):
        # transform to feature matrix
        # ...first find out how many columns and rows the feature matrix will have
        numFeatures = 0
        numPoints = overlays[0].shape[0] * overlays[0].shape[1] * overlays[0].shape[2] * overlays[0].shape[3]
        for overlay in overlays:
            numFeatures += overlay.shape[4]
        # ... then copy the data
        features = numpy.zeros((numPoints, numFeatures), dtype=numpy.float)
        currFeature = 0
        for overlay in overlays:
            currData = overlay[:,:,:,:,:]
            features[:, currFeature:currFeature+overlay.shape[4]] = currData.reshape(numPoints, (currData.shape[4]))
            currFeature += currData.shape[4]
        self.features = features
        self.origshape = overlays[0].shape
        
    def decompose(self):
        # V contains the component spectra/scores, W contains the projected data
        unsupervisedMethod = self.unsupervisedMethod()
        V, W = unsupervisedMethod.decompose(self.features)
        self.result = (W.T).reshape((self.origshape[0], self.origshape[1], self.origshape[2], self.origshape[3], W.shape[0]))

    def run(self):
        self.dataMgr.featureLock.acquire()
        try:
            jobs = []
            job = jobMachine.IlastikJob(UnsupervisedDecompositionThread.decompose, [self])
            jobs.append(job)
            self.jobMachine.process(jobs)
            self.dataMgr.featureLock.release()
        except Exception, e:
            print "######### Exception in UnsupervisedThread ##########"
            print e
            traceback.print_exc(file=sys.stdout)
            self.dataMgr.featureLock.release()
            
    