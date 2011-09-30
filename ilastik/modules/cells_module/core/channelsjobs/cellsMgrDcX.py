import vigra
import numpy
import h5py


from scipy import ndimage
import gc

from ilastik.core.dataMgr import DataMgr, DataItemImage
from ilastik.modules.classification.core.featureMgr import FeatureMgr
from ilastik.modules.classification.core.features.featureBase import FeatureBase
from ilastik.modules.classification.core.classificationMgr import ClassifierPredictThread, ClassificationModuleMgr
from ilastik.core.volume import DataAccessor
from ilastik.core.jobMachine import JobMachine, IlastikJob


from ilastik.modules.cells_module.core.Auxiliary import *

    
            
class DcxSegmentation(object):
    """decide weather a cell is positive or not"""
    def __init__(self,dictPositions,weights,fileNameToClassifier):
        self.d=dictPositions
        self.weights=weights
        self.getAverageIntensityPerSlice()
        self.fileNameToClassifier=fileNameToClassifier
        
        self.SetDictIntDcX() #set the average Luminescence value into the dcx channel
        
        self.dictPositiveCells={}
        self.segment()
        self.setDictPositiveCells()
    
    def segment(self):
        #create a new internal Data manager
        
        dataMgr = DataMgr()
        
        # Add data item di to dataMgr
        di = DataItemImage('')
        di.setDataVol(DataAccessor(self.weights))
        dataMgr.append(di, alreadyLoaded=True)
        
        # Load classifier from hdf5
        try:
            classifiers = ClassificationModuleMgr.importClassifiers(self.fileNameToClassifier)
        except:
            raise RuntimeError('cannot Load Classifier ' + self.fileNameToClassifier)
        
        dataMgr.module["Classification"]["classificationMgr"].classifiers = classifiers                 


        # Restore user selection of feature items from hdf5
        featureItems = []
        f = h5py.File(self.fileNameToClassifier, 'r')
        for fgrp in f['features'].values():
            featureItems.append(FeatureBase.deserialize(fgrp))
        f.close()
        del f
        
        # Create FeatureMgr
        fm = FeatureMgr(dataMgr, featureItems)
        
        # Compute features
        fm.prepareCompute(dataMgr)
        fm.triggerCompute()
        fm.joinCompute(dataMgr)

        # Predict with loaded classifier
        
        classificationPredict = ClassifierPredictThread(dataMgr)
        classificationPredict.start()
        classificationPredict.wait()

        # Produce output image and select the probability map
        self.probMap = []
        self.probMap = classificationPredict._prediction[0][0,:,:,:,0].copy()
        
        #clean up the memory
        
        del classifiers
        del classificationPredict
        del dataMgr  
        del fm
        del di
        del featureItems
        gc.collect()
        
        self.segmented=(self.probMap>0.5)

        
        self.segmented=self.segmented.astype(numpy.uint8)
        #self.segmented=vigra.filters.discClosing(self.segmented,1)
        self.segmented=self.segmented.astype(numpy.uint8).view(numpy.ndarray) 
    
      
    def SetDictIntDcX(self):
        print "Calculating Cell Average intensity Dcx Channel"
        self.DictIntDcX={}
        
        for k in self.d.iterkeys():
            self.DictIntDcX[k]=float(numpy.mean(self.weights[self.d[k][0],self.d[k][1],self.d[k][2]]))         

    def setDictPositiveCells(self):
        for k in self.d.iterkeys():
            self.dictPositiveCells[k]=numpy.mean(self.segmented[self.d[k][0],self.d[k][1],self.d[k][2]])>0.4
            print "is the cell positive? " , self.dictPositiveCells[k], numpy.mean(self.segmented[self.d[k][0],self.d[k][1],self.d[k][2]])
            
            
    def getAverageIntensityPerSlice(self):
        self.averageIntSlice=numpy.zeros(self.weights.shape[2])
        for i in range(self.weights.shape[2]):
            self.averageIntSlice[i]=self.weights[:,:,i].mean()



#test
if __name__ == "__main__":
    import os, sys, numpy,pickle,pprint
    path=os.path.dirname(sys.argv[0])
    print path
    testdata=vigra.impex.readVolume(path+'/testDcXImages/C3-lif_to_test_ana0000.tif')
    testdata = vigra.filters.gaussianSmoothing(testdata.astype(numpy.float32), 2)
    testdata = vigra.sampling.resizeVolumeSplineInterpolation(testdata,(512,512,15))
    print "smoothed"
    f=open('DictPositions.pkl','rb')
    d=pickle.load(f)
    pprint.pprint(d)
    f.close()
    Dcx=DcxSegmentation(d,testdata.view(numpy.ndarray).astype(numpy.float32))
    pprint.pprint(Dcx.DictIntDcX)
    pprint.pprint(Dcx.averageIntSlice)
    
