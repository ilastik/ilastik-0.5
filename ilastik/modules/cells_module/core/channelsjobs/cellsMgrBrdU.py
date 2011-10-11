import vigra
import numpy
import h5py



import gc

from ilastik.core.dataMgr import DataMgr, DataItemImage
from ilastik.modules.classification.core.featureMgr import FeatureMgr
from ilastik.modules.classification.core.features.featureBase import FeatureBase
from ilastik.modules.classification.core.classificationMgr import ClassifierPredictThread, ClassificationModuleMgr
from ilastik.core.volume import DataAccessor
from ilastik.core.jobMachine import JobMachine, IlastikJob

from ilastik.modules.cells_module.core.Auxiliary import *



class BrdUSegmentation(object):
    
    def __init__(self, weights, fileNameToClassifier,maskForFilter,physicalSize=(0.7576*2,0.7576*2,1/2.0),sigmaPmap=0.2,sigmaWeights=2):
        
        self.physSize=physicalSize
        self.voxelVol=physicalSize[0]*physicalSize[1]*physicalSize[2]
        
        print "Physical Size", self.physSize
        
        self.sigmaP=sigmaPmap #smooth the pamp before watershed
        self.sigmaW=sigmaWeights #smooth the pamp before watershed
        
        #internal stastes
        self.weights=weights.view(numpy.ndarray)
        self.mask=maskForFilter
        self.fileNameToClassifier=fileNameToClassifier
        self.probMap = None
        self.segmented=None     #segmented cells
        self.averageIntSlice=None #average intensity per slice into this channel
        
        self.DictCenters={}
        self.DictIntBrdU={}
        self.DictPositions={}
        
        self.distanceMatrix=None
        
        self.filterRadius=1.5 #Radius of the filter to smooth the original image or the probabilty map
        #Start
        
        self._exec()
        
        
    def _exec(self):     
        
        
        self.getAverageIntensityPerSlice()
        self.CreateProbMap()
        
        self.CellsSegmentationFromProbmap()
        #self.probMap=None #throw out the pmap
        gc.collect()
        
        #self.DictPositions=PositionsDictionary3D.setdict(self.segmented)
        #print "GGGGGGGUGAG",self.DictPositions
        self.FilterByOverlap()  #filters the cells on the overlap with gyrus and interior
        self.DictPositions=PositionsDictionary3D.setdict(self.segmented)
        #print "GGGGGGGUGAG",self.DictPositions
        
        self.FilterBySize()                                             
        #print "GGGGGGGUGAG2",self.DictPositions
        
        
        self.SetDictIntBrdU() #set the dictionary with the Cell average BrdU luminescence value
        self.SetDictCenters()
        self.computeDistanceMatrix()
                                                     
    def CreateProbMap(self):
        #create a new internal Data manager
        
        dataMgr = DataMgr()
        
        # Add data item di to dataMgr
        di = DataItemImage('')
        try:
            di.setDataVol(DataAccessor(self.weights))
        except Exception,e:
            print e
            raise
        
        dataMgr.append(di, alreadyLoaded=True)
        
        #print "Here2"
        
        # Load classifier from hdf5
        try:
            print "Loading the classifier ", self.fileNameToClassifier
            #print type(self.fileNameToClassifier)
            classifiers = ClassificationModuleMgr.importClassifiers(self.fileNameToClassifier)
            #print "passato"
        except Exception,e:
            print e
            raise
            
        try:
            dataMgr.module["Classification"]["classificationMgr"].classifiers = classifiers                 
        except Exception,e:
            print e
            raise
        
        #print "Here3"

        # Restore user selection of feature items from hdf5
        featureItems = []
        f = h5py.File(self.fileNameToClassifier, 'r')
        for fgrp in f['features'].values():
            featureItems.append(FeatureBase.deserialize(fgrp))
        f.close()
        del f
        # print "Here4"
        # Create FeatureMgr
        fm = FeatureMgr(dataMgr, featureItems)
        #print "Here5"
        # Compute features
        fm.prepareCompute(dataMgr)
        fm.triggerCompute()
        fm.joinCompute(dataMgr)

        # Predict with loaded classifier
        #print "Here6"
        classificationPredict = ClassifierPredictThread(dataMgr)
        classificationPredict.start()
        classificationPredict.wait()

        # Produce output image and select the probability map
        self.probMap = []
        self.probMap = classificationPredict._prediction[0][0,:,:,:,0].copy().view(numpy.ndarray)
        
        #clean up the memory
        
        del classifiers
        del classificationPredict
        del dataMgr  
        del fm
        del di
        del featureItems
        gc.collect()
        
        try:
            self.probMap=vigra.filters.gaussianSmoothing(self.probMap,self.sigmaP).view(numpy.ndarray).squeeze()
        except:
            try:
                print "Warning!!!! the shape of the input is really small ", self.weights.shape
                self.probMap=vigra.filters.gaussianSmoothing(self.probMap,self.sigmaP/2.0).view(numpy.ndarray).squeeze()
            except Exception,e:
                print e
                pass
        self.probMap=numpy.require(self.probMap,numpy.float32).view(numpy.ndarray)
        
        
    def CellsSegmentationFromProbmap(self,bgmThresh=0.40):
        """segment the cells from the probability map
        assumes that the label of the cells is 0"""
        self.weights=numpy.require(self.weights,numpy.float32)
        
        try:
            self.weights=vigra.filters.gaussianSmoothing(self.weights,self.sigmaW).view(numpy.ndarray).squeeze()
        except Exception,e:
            print e
            try:
                print "Warning!!!! the shape of the input pmap is really small ", self.weights.shape
                self.weights=vigra.filters.gaussianSmoothing(self.weights,self.sigmaW/2.0).view(numpy.ndarray).squeeze()
            except:
                self.weights=self.weights.astype(numpy.float32)
                print self.weights.shape
        fgm = vigra.analysis.extendedLocalMaxima3D(self.weights,1.0)
        
        
        fgm[numpy.where(self.probMap < bgmThresh)] = 0 #delete small maxima
        
        fgm1 = vigra.analysis.labelVolumeWithBackground(fgm, 6, float(0)) #marca i massimi in differenti label
        
        bgm = (self.probMap < bgmThresh).astype(numpy.float32)
        bgm1 = vigra.analysis.labelVolumeWithBackground(bgm, 6, float(0))
            
        
        bgmMaxLabel = int(bgm1.max())               #differentiate the seeds
        fgm1[numpy.where(fgm1 > 0)] += bgmMaxLabel
        seeds = (bgm1 + fgm1).astype(numpy.uint32)
        
        #crappy stuff needed to avoid crashing vigra
        
        self.segmented = vigra.analysis.watersheds(self.probMap, 6, seeds)[0]     
        self.segmented[numpy.where(self.segmented <= bgmMaxLabel)] = 0
        self.segmented[numpy.where(self.segmented > bgmMaxLabel)] -= bgmMaxLabel
        
        
        #print "OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOHJGhjfghdsfghdsagf ",self.segmented.max()        
        #vigra.impex.writeVolume(self.segmented*255,'/home/lfiaschi/Desktop/test/00.png')

    def getAverageIntensityPerSlice(self):
        self.averageIntSlice=numpy.zeros(self.weights.shape[2])
        for i in range(self.weights.shape[2]):
            self.averageIntSlice[i]=self.weights[:,:,i].mean()
    
    
    def FilterByOverlap(self):
        #to do : implement a margin
        print "Filtering Cells by Overlap with Gyrus and Interior"
        #print "GGGGGGGGGGGGGGGGGGGGGGGGG",self.mask.shape
        #print "FFFFFFFFFFFFFFFFFFFFFFFF",self.segmented.shape
        #print "BEFOREFILTERINGOOOOHJGhjfghdsfghdsagf ",self.segmented.max() 
        #vigra.impex.writeVolume((self.mask*255).astype(numpy.uint8),'/home/lfiaschi/Desktop/test/test0','.tif')
        #vigra.impex.writeVolume((self.segmented*255).astype(numpy.uint8),'/home/lfiaschi/Desktop/test/othertest0','.tif')
        self.segmented[self.mask==0]=0 #put zero if they do not overlap with Gyrus  
        self.segmented=self.segmented.astype(numpy.float32)
        self.segmented=vigra.analysis.labelVolumeWithBackground(self.segmented,6)
        #print "FILTERINGOOOOHJGhjfghdsfghdsagf ",self.segmented.max() 
    
    
       
    
    def FilterBySize(self,filter=(6,1500)):
        print "Filtering Cells by Size"
        d={}
        t=self.DictPositions
        
                
        minbound=filter[0]
        maxbound=filter[1]
        temp=numpy.zeros(self.segmented.shape,dtype=numpy.uint32)
        
        i=1
        for k in t.iterkeys():
            if minbound<len(t[k][0]) and len(t[k][0])<maxbound :
                d[i]=t[k]

                temp[d[i][0],d[i][1],d[i][2]]=i
                i=i+1
        
        
        self.DictPositions=d  
        self.segmented=temp
    
     
    def SetDictIntBrdU(self):
        """Add the average BrdU luminescence value"""
        print "Calculating Average Intensity BrdU channel "
        self.DictIntBrdU={}
        for k in self.DictPositions.iterkeys():
            self.DictIntBrdU[k]=float(numpy.mean(self.weights[self.DictPositions[k][0],self.DictPositions[k][1],self.DictPositions[k][2]]))
       
 
    def SetDictCenters(self):
   
        self.DictCenters={}
        
        d=self.DictPositions #TODO remove d
        
        print "Centers coordinates"
        
        for k in d.iterkeys():
            
            temp=numpy.zeros((3,len(d[k][0])))
            temp[0,:]=d[k][0]
            temp[1,:]=d[k][1]
            temp[2,:]=d[k][2]
            
            
            temp=temp.mean(axis=1)
            
            
            
            temp[0]=round(temp[0])
            temp[1]=round(temp[1])
            temp[2]=round(temp[2])
                          
            self.DictCenters[k]=temp
            print self.DictCenters[k]  
 


    def computeDistanceMatrix(self):
        self.distanceMatrix=computeDistanceMatrix(self.DictCenters,self.physSize)



#TEST

if __name__ == "__main__":
    import os, sys, numpy,pickle
    path=os.path.dirname(sys.argv[0])
    print path+'/testBrdUImages/ch1.ilp'
    
     
    try:
        h=h5py.File(path+'/testBrdUImages/ch1.ilp','r')
    except Exception,e:
        
        print path+'/testBrdUImages/ch1.ilp'
        print e
        raise
    
    testdata=numpy.array(h['DataSets/dataItem00/data'][:,:,:,:,:])
    testdata=testdata.squeeze()
    #vigra.impex.writeVolume(testdata,path+'/testBrdUImages/ResultTest/original_before','.tif')
    g=vigra.impex.readVolume(path+'/testDapyImages/GroundTruth/gyrus00.tif').view(numpy.ndarray).squeeze()
    i=vigra.impex.readVolume(path+'/testDapyImages/GroundTruth/interior00.tif').view(numpy.ndarray).squeeze()
    print "The testdata !!!", testdata.shape,  testdata.dtype, type(testdata)

    

    Cells=BrdUSegmentation(testdata.view(numpy.ndarray).astype(numpy.float32),path+'/testBrdUImages/ch1_classifier.h5',g+i,)
    vigra.impex.writeVolume(Cells.weights.astype(numpy.uint8),path+'/testBrdUImages/ResultTest/original','.tif')
    vigra.impex.writeVolume(Cells.segmented.astype(numpy.uint8)*255,path+'/testBrdUImages/ResultTest/segmented','.tif')
    
    
    
    print "Numbure of cells ", len(Cells.DictPositions)

 
 