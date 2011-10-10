# -*- coding: utf-8 -*-
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





class GyrusSegmentation(object):
    def __init__(self,weights=None, filenametoclassifier='',physicalSize=(0.7576*2,0.7576*2,1/2.0)):
        
        self.physSize=physicalSize
        print "Physical Size", self.physSize
        self.voxelVol=physicalSize[0]*physicalSize[1]*physicalSize[2]
        
        self.interior=None    #contains the interior in self res
        self.weights=weights

        self.setParameters({'smooth_before': 'False','filter_radius': 2.0, 'fileNameToClassifier': filenametoclassifier  }) 
        self._exec()
    
    def _exec(self):
        
        """Nb a istance of this class contains the interior in self.res"""
        
       
        self.getAverageIntensityPerSlice()
        self.smooth()  #Smooth the image append self.smoothed
        
        self.segment() #Segment the image append self.segmented

        self.removeSmallImpurities() #to eliminte small false positive that could disturb the hull
        self.getGyrusVolume()
        self.getGyrusAreaPerSlice()
        
        
        self.Hull()    #Calculate the hulll append self.res that contains the interiot
        self.distanceTransform()  #calculate the distance transform  append self.distancetransformed  
        #get some interesting data
        self.getInteriorAreaPerSlice()
        self.getInteriorVolume()
        
        self.res=self.interior
    
    def setParameters(self, paramsDict):
        self.__dict__.update(paramsDict)
        
    def smooth(self): #Maybe to implement Gaussian smoothing later
        
        if self.smooth_before=='False':
            self.smoothed=self.weights.astype(numpy.float32)
        else:
            self.smoothed = vigra.filters.gaussianSmoothing(self.weights.astype(numpy.float32),0.5)          
        
    def segment(self):
        #create a new internal Data manager
        #print "Here1"
        dataMgr = DataMgr()
        
        # Add data item di to dataMgr
        di = DataItemImage('')
        try:
            di.setDataVol(DataAccessor(self.smoothed))
        except Exception,e:
            print self.smoothed.shape
            print self.smoothed.dtype 
            print e
        
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
            
        try:
            dataMgr.module["Classification"]["classificationMgr"].classifiers = classifiers                 
        except Exception,e:
            print e
        
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
        self.probMap = classificationPredict._prediction[0][0,:,:,:,0].copy()
        #vigra.impex.writeVolume(self.probMap,'prova_pMap','.tif')
        #clean up the memory
        
        del classifiers
        del classificationPredict
        del dataMgr  
        del fm
        del di
        del featureItems
        gc.collect()
        
        #self.probMap=vigra.filters.gaussianSmoothing(self.probMap,(2,2,0)).view(numpy.ndarray)
        self.probMap=self.probMap.view(numpy.ndarray).astype(numpy.float32)
        for z in range(self.probMap.shape[-1]):
            self.probMap[:,:,z]=vigra.filters.gaussianSmoothing(self.probMap[:,:,z],2).view(numpy.ndarray).squeeze()
        self.segmented=(self.probMap>0.5)
        self.segmented=self.segmented.astype(numpy.uint8)
        #self.segmented=vigra.filters.discClosing(self.segmented,4)
        self.segmented=self.segmented.astype(numpy.uint8).view(numpy.ndarray)
        #self.segmented=vigra.filters.discErosion(self.segmented,2).view(numpy.ndarray).astype(numpy.uint8)
        
    def removeSmallImpurities(self):
        """Remove Small impurities ad get the Gyrus Volume"""

        for i in range(self.segmented.shape[2]):
            try:
        		temp=vigra.analysis.labelImageWithBackground(self.segmented[:,:,i])
        		sizes=numpy.bincount(temp.flatten())
        		sizes=sizes[1:]
        		index=sizes.argmax()+1
        		temp=numpy.where(temp==index,1,0)
        		self.segmented[:,:,i]=temp
        		
        		"""
        		index=sizes.argsort()[::-1] + 1
        		print index
        		
        		
        		print index[0]==sizes.argmax()+1
        		print index[0],sizes.argmax()+1
        		
        		T=50000
        		newindex=[]
        		for ind in index:
        		    if sizes[ind-1]>T: newindex.append(ind)
        		print "newindex", newindex
        		
        		temp2=numpy.zeros(temp.shape)
        		for ind in newindex: temp2[numpy.where(temp==ind)]=1
        		self.segmented[:,:,i]=temp2
        		vigra.impex.writeImage(self.segmented[:,:,i]*255,'test' +str(i)+'.tiff')
        		"""
        		
        		
        	    
        		#print "warning empty sequence found"
        		#pass
            except Exception,e:
                print 'No gyrus found'
                print e
                pass
        
        
    def getGyrusVolume(self):
        self.GyrusVolume=self.segmented.sum()*self.voxelVol    #volume of the Gyrus
            
            
             
           
    def Hull(self):
        """ find the set of points that define the Hulll"""
        
        self.interior=numpy.zeros(self.weights.shape,'uint8') #the vector that contains the interior        
        
        for i in range(self.weights.shape[2]):
	        #vigra.impex.writeVolume(self.segmented*255,path+'/testDapyImages/ResultTest/interior_before','.tif')
            
            H=Hull2DObject()
            self.interior[:,:,i]=H.calculate(self.segmented[:,:,i].view(numpy.ndarray))
            #vigra.impex.writeImage(H.mask*255,path+'/testDapyImages/ResultTest/mask'+str(i)+'.tif')
            #self.res[:,:,i]=Hull2DObject().calculate(self.segmented[:,:,i].view(numpy.ndarray))
            
	        #vigra.impex.writeVolume(self.res*255,path+'/testDapyImages/ResultTest/interior_before','.tif')
            
    def distanceTransform(self):
        self.interior=numpy.require(self.interior,numpy.float32)
        self.interior=self.interior.view(numpy.ndarray)
        self.distanceTransformed=numpy.zeros(self.interior.shape, "float32")
        for i in range(self.interior.shape[2]):
            self.distanceTransformed[:,:,i]=vigra.filters.distanceTransform2D(self.interior[:,:,i]).view(numpy.ndarray)*self.physSize[0]
            
    
    def getGyrusAreaPerSlice(self):
        self.GyrusArea=numpy.zeros(self.weights.shape[2])
        for i in range(self.weights.shape[2]):
            self.GyrusArea[i]=self.segmented[:,:,i].sum()*self.physSize[0]*self.physSize[1]    
  
    def getInteriorAreaPerSlice(self):
        self.InteriorArea=numpy.zeros(self.interior.shape[2])
        for i in range(self.interior.shape[2]):
            self.InteriorArea[i]=self.interior[:,:,i].sum()*self.physSize[0]*self.physSize[1]
            
    def getAverageIntensityPerSlice(self):
        self.averageIntSlice=numpy.zeros(self.weights.shape[2])
        for i in range(self.weights.shape[2]):
            self.averageIntSlice[i]=self.weights[:,:,i].mean()

    def getInteriorVolume(self):
        self.InteriorVolume=self.interior.sum()*self.voxelVol      






#TEST

if __name__ == "__main__":
    import os, sys, numpy,h5py
    path=os.path.dirname(sys.argv[0])
    print path
    
    try:
        h=h5py.File(path+'/testDapyImages/ch0.ilp','r')
    except Exception,e:
        
        print path+'/ch0.ilp'
        print e
        raise
    
    testdata=numpy.array(h['DataSets/dataItem00/data'][:,:,:,:,:])
    testdata=testdata.squeeze()
    print testdata.shape
    h.close()
    
    #testdata=vigra.impex.readVolume(path+'/testDapyImages/C1-lif_to_test_ana0000.tif')
    
    print "The Tesdata!!!", testdata.shape,  testdata.dtype, type(testdata)
    #testdata = vigra.filters.gaussianSmoothing(testdata.astype(numpy.float32), 2)
    #testdata = vigra.sampling.resizeVolumeSplineInterpolation(testdata,(512,512,15))
    #print "smoothed"
    Gyrus=GyrusSegmentation(testdata.view(numpy.ndarray).astype(numpy.float32),filenametoclassifier=path+'/testDapyImages/ch0_classifier.h5')
    #print type(Gyrus.res)
    vigra.impex.writeVolume(Gyrus.res*255,path+'/testDapyImages/ResultTest/interior','.tif')
    vigra.impex.writeVolume(Gyrus.segmented*255,path+'/testDapyImages/ResultTest/gyrus','.tif')
    print "Interior Volume ", Gyrus.InteriorVolume
    print "Interior Area ", Gyrus.InteriorArea
    print "Gyrus Area ", Gyrus.GyrusArea
    print "Gyrus Volume ", Gyrus.GyrusVolume
    
    print "Comparing the results"
    
    groundInterior=vigra.impex.readVolume(path+'/testDapyImages/GroundTruth/interior00.tif').view(numpy.ndarray).squeeze()
    print groundInterior.shape,groundInterior.dtype
    print Gyrus.interior.shape,Gyrus.interior.dtype
    numpy.testing.assert_array_equal(groundInterior,Gyrus.res*255)
    
    groundGyrus=vigra.impex.readVolume(path+'/testDapyImages/GroundTruth/gyrus00.tif').view(numpy.ndarray).squeeze()
    numpy.testing.assert_array_equal(groundGyrus,Gyrus.segmented*255)
    
    print "ok!"
       