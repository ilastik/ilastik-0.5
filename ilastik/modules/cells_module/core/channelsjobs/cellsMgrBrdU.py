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



class BrdUSegmentation(object):
    
    def __init__(self, weights, fileNameToClassifier,maskForFilter,physicalSize=(0.7576*2,0.7576*2,1/2)):
        
        self.physSize=physicalSize
        self.voxelVol=physicalSize[0]*physicalSize[1]*physicalSize[2]
        
        print "Physical Size", self.physSize
        
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
        self.probMap=None #throw out the pmap
        gc.collect()
        
        
        self.FilterByOverlap()  #filters the cells on the overlap with gyrus and interior
        self.DictPositions=PositionsDictionary3D.setdict(self.segmented)
        self.FilterBySize()                                             
        
        self.SetDictIntBrdU() #set the dictionary with the Cell average BrdU luminescence value
        self.SetDictCenters()
        self.computeDistanceMatrix()
                                                     
    def CreateProbMap(self):
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
            raise RuntimeError('unable to open the file ' + self.fileNameToClassifier)
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
        
        self.probMap = classificationPredict._prediction[0][0,:,:,:,0].copy()
        
        #clean up the memory
        
        del classifiers
        del classificationPredict
        del dataMgr  
        del fm
        del di
        del featureItems
        gc.collect()
        


        
        
    def CellsSegmentationFromProbmap(self,bgmThresh=0.5):
        """segment the cells from the probability map
        assumes that the label of the cells is 0"""
        try:
            self.weights=vigra.filters.gaussianSmoothing(self.weights.astype(numpy.float32),1.00).view(numpy.ndarray)
        except:
            self.weights=vigra.filters.gaussianSmoothing(self.weights.astype(numpy.float32),0.5).view(numpy.ndarray)
        
        fgm = vigra.analysis.extendedLocalMaxima3D(self.weights,1)
        
        
        
        fgm[numpy.where(self.probMap < bgmThresh)] = 0 #delete small maxima
        
        fgm1 = vigra.analysis.labelVolumeWithBackground(fgm, 6, float(0)) #marca i massimi in differenti label
        
    
        
        bgm = (self.probMap < bgmThresh).astype(numpy.float32)
        bgm1 = vigra.analysis.labelVolumeWithBackground(bgm, 6, float(0))
            
        
        bgmMaxLabel = int(bgm1.max())               #differentiate the seeds
        fgm1[numpy.where(fgm1 > 0)] += bgmMaxLabel
        seeds = (bgm1 + fgm1).astype(numpy.uint32)
        
        #crappy stuff needed to avoid crashing vigra
        try:
            self.segmented = vigra.analysis.watersheds(vigra.filters.gaussianGradientMagnitude(self.probMap, 1), 6, seeds)[0]
        except:
            try:
                self.segmented = vigra.analysis.watersheds(vigra.filters.gaussianGradientMagnitude(self.probMap, 0.5), 6, seeds)[0]
                print "avoiding crash of vigra, inside CellsMgrBrdU with sigma 0.3"
            except:
                self.segmented = vigra.analysis.watersheds(vigra.filters.gaussianGradientMagnitude(self.probMap, 0.1), 6, seeds)[0]
                print "avoiding crash of vigra, inside CellsMgrBrdU with sigma 0.1"
        
        self.segmented[numpy.where(self.segmented <= bgmMaxLabel)] = 0
        self.segmented[numpy.where(self.segmented > bgmMaxLabel)] -= bgmMaxLabel
        
        
        
        

    def getAverageIntensityPerSlice(self):
        self.averageIntSlice=numpy.zeros(self.weights.shape[2])
        for i in range(self.weights.shape[2]):
            self.averageIntSlice[i]=self.weights[:,:,i].mean()
    
    
    def FilterByOverlap(self):
        #to do : implement a margin
        print "Filtering Cells by Overlap with Gyrus and Interior"
        self.segmented[self.mask==0]=0 #put zero if they do not overlap with Gyrus  
        self.segmented=self.segmented.astype(numpy.float32)
        self.segmented=vigra.analysis.labelVolumeWithBackground(self.segmented,6)
    
    
    
       
    
    def FilterBySize(self,filter=(15,1500)):
        print "Filtering Cells by Size"
        d={}
        t=self.DictPositions
        
                
        minbound=filter[0]
        maxbound=filter[1]
        temp=numpy.zeros(self.segmented.shape,dtype=numpy.uint8)
        
        i=1
        for k in t.iterkeys():
            if minbound<len(t[k][0]) and len(t[k][0])<maxbound :
                d[i]=t[k]

                temp[d[i][0],d[i][1],d[i][2]]=i
                i=i+1
        
        if i>255: raise RunTimeError('too Many cells') 
        
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
    print path+ '/testDapyImages/NesCreDkk1 No2 Slice 1_series_0_CH_1.h5'
    
    try:
        h=h5py.File(path+'/testBrdUImages/NesCreDkk1 No2 Slice 1_series_0_CH_1.h5','r')
    except:
        raise
    
    testdata=numpy.array(h['volume/data'][:,:,:,:15,:])
    testdata=testdata.squeeze()
    #vigra.impex.writeVolume(testdata,path+'/testBrdUImages/ResultTest/original_before','.tif')
    g=vigra.impex.readVolume(path+'/testBrdUImages/Gyrus_mask/gyrus00.tif')
    i=vigra.impex.readVolume(path+'/testBrdUImages/Gyrus_mask/interior00.tif')
    print "The testdata !!!", testdata.shape,  testdata.dtype, type(testdata)

    

    Cells=BrdUSegmentation(testdata.view(numpy.ndarray).astype(numpy.float32),path+'/testBrdUImages/classifiersCells_new',g+i,)
    vigra.impex.writeVolume(Cells.weights.astype(numpy.uint8),path+'/testBrdUImages/ResultTest/original','.tif')
    vigra.impex.writeVolume(Cells.segmented.astype(numpy.uint8)*255,path+'/testBrdUImages/ResultTest/segmented','.tif')
    
    
    
    print "Numbure of cells ", len(Cells.DictPositions)
    
    output=open(path+'/testBrdUImages/ResultTest/DictPositions.pkl','wb')
    pickle.dump(Cells.DictPositions, output)
    output.close()
    temp=numpy.zeros((972, 512, 15,3),dtype=numpy.uint8)
    
    temp[:,:,:,0]=Cells.weights.astype(numpy.uint8)
    temp[:,:,:,1]=Cells.segmented.astype(numpy.uint8)*255
    
    print "Here", temp.shape
    for i in range(15):
        vigra.impex.writeImage(temp[:,:,i,:],path+'/testBrdUImages/ResultTest/colored'+str(i)+'.tif')
    
    print "print dict int BrdU",  Cells.DictIntBrdU
    print "print dict Centers", Cells.DictCenters
    
 
 