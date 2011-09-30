# -*- coding: utf-8 -*-
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





class GyrusSegmentation(object):
    def __init__(self,weights=None,use3D=None, filenametoclassifier='',physicalSize=(0.7576*2,0.7576*2,1/2)):
        
        self.physSize=physicalSize
        print "Physical Size", self.physSize
        self.voxelVol=physicalSize[0]*physicalSize[1]*physicalSize[2]
        
        self.res=None    #contains the interior in self res
        self.weights=weights

        self.setParameters({'smooth_before': 'False','filter_radius': 2.0,'use3D':use3D,  'fileNameToClassifier': filenametoclassifier  }) 
        self._exec()
    
    def _exec(self):
        
        """Nb a istance of this class contains the interior in self.res"""
        
       
        self.getAverageIntensityPerSlice()
        self.smooth()  #Smooth the image append self.smoothed
        
        self.segment() #Segment the image append self.segmented

        self.removeSmallImpurities() #to eliminte small false positive that could disturb the hull
        self.Hull()    #Calculate the hulll append self.res that contains the interiot
        self.distanceTransform()  #calculate the distance transform  append self.distancetransformed  
        
        #get some interesting data
        self.getGyrusVolume()
        self.getGyrusAreaPerSlice()
        self.getInteriorAreaPerSlice()
        self.getInteriorVolume()
    
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
        except:
            print self.smoothed.shape
            print self.smoothed.dtype 
            raise RuntimeError('Cannot Append the data')
        dataMgr.append(di, alreadyLoaded=True)
        
        #print "Here2"
        
        # Load classifier from hdf5
        try:
            #print self.fileNameToClassifier
            #print type(self.fileNameToClassifier)
            classifiers = ClassificationModuleMgr.importClassifiers(self.fileNameToClassifier)
            #print "passato"
        except:
            raise RuntimeError('cannot Load Classifier ' +self.fileNameToClassifier)
        
        try:
            
            dataMgr.module["Classification"]["classificationMgr"].classifiers = classifiers                 
        except:
            raise RuntimeError('cannot append the classfiers')
        
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
        self.segmented=(self.probMap>0.5)

        
        self.segmented=self.segmented.astype(numpy.uint8)
        self.segmented=vigra.filters.discClosing(self.segmented,4)
        self.segmented=self.segmented.astype(numpy.uint8).view(numpy.ndarray)
	self.segmented=vigra.filters.discErosion(self.segmented,2)
    def removeSmallImpurities(self):
        """Remove Small impurities ad get the Gyrus Volume"""

        for i in range(self.segmented.shape[2]):
            try:
        		temp=vigra.analysis.labelImageWithBackground(self.segmented[:,:,i])
        		sizes=numpy.bincount(temp)
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
            except:
        		print 'No gyrus found'
        		pass
        
        
    def getGyrusVolume(self):
        self.GyrusVolume=self.segmented.sum()*self.voxelVol    #volume of the Gyrus
            
            
             
           
    def Hull(self):
        """ find the set of points that define the Hulll"""
        
        self.res=numpy.zeros(self.weights.shape,'uint8') #the vector that contains the interior        
        
        for i in range(self.weights.shape[2]):
	    #vigra.impex.writeVolume(self.segmented*255,path+'/testDapyImages/ResultTest/interior_before','.tif')
            
            H=Hull2DObject()
            self.res[:,:,i]=H.calculate(self.segmented[:,:,i].view(numpy.ndarray))
            #vigra.impex.writeImage(H.mask*255,path+'/testDapyImages/ResultTest/mask'+str(i)+'.tif')
            #self.res[:,:,i]=Hull2DObject().calculate(self.segmented[:,:,i].view(numpy.ndarray))
            
	    #vigra.impex.writeVolume(self.res*255,path+'/testDapyImages/ResultTest/interior_before','.tif')
            
    def distanceTransform(self):
        if self.use3D==True or self.use3D==None:
            self.distanceTransformed=vigra.filters.distanceTransform3D(self.res.astype(numpy.float32)) #distance trasform of the gyrus interier
            self.distanceTransformed=self.distanceTransformed - vigra.filters.distanceTransform3D(1-self.res.astype(numpy.float32))*self.physSize[0]*self.physSize[1]
        else:
            raise
            self.distanceTransformed=numpy.zeros(self.res.shape, "float32")
            for i in range(self.res.shape[2]):
                self.distanceTransformed[:,:,i]=vigra.filters.distanceTransform2D(self.res[:,:,i].view(numpy.ndarray).astype(numpy.float32))
            
    
    def getGyrusAreaPerSlice(self):
        self.GyrusArea=numpy.zeros(self.weights.shape[2])
        for i in range(self.weights.shape[2]):
            self.GyrusArea[i]=self.segmented[:,:,i].sum()*self.physSize[0]*self.physSize[1]    
  
    def getInteriorAreaPerSlice(self):
        self.InteriorArea=numpy.zeros(self.weights.shape[2])
        for i in range(self.weights.shape[2]):
            self.InteriorArea[i]=self.res[:,:,i].sum()*self.physSize[0]*self.physSize[1]
            
    def getAverageIntensityPerSlice(self):
        self.averageIntSlice=numpy.zeros(self.weights.shape[2])
        for i in range(self.weights.shape[2]):
            self.averageIntSlice[i]=self.weights[:,:,i].mean()

    def getInteriorVolume(self):
        self.InteriorVolume=self.res.sum()*self.voxelVol      






#TEST

if __name__ == "__main__":
    import os, sys, numpy,h5py
    path=os.path.dirname(sys.argv[0])
    print path
    
    try:
        h=h5py.File(path+'/testDapyImages/NesCreDkk1 No2 Slice 1_series_0_CH_0.h5','r')
    except:
        raise
    
    testdata=numpy.array(h['volume/data'][:,:,:,:15,:])
    testdata=testdata.squeeze()
    
    h.close()
    
    #testdata=vigra.impex.readVolume(path+'/testDapyImages/C1-lif_to_test_ana0000.tif')
    
    print "The Tesdata!!!", testdata.shape,  testdata.dtype, type(testdata)
    #testdata = vigra.filters.gaussianSmoothing(testdata.astype(numpy.float32), 2)
    #testdata = vigra.sampling.resizeVolumeSplineInterpolation(testdata,(512,512,15))
    #print "smoothed"
    Gyrus=GyrusSegmentation(testdata.view(numpy.ndarray).astype(numpy.float32),use3D='None',filenametoclassifier=path+'/testDapyImages/classifierGyrus.h5')
    #print type(Gyrus.res)
    vigra.impex.writeVolume(Gyrus.res*255,path+'/testDapyImages/ResultTest/interior','.tif')
    vigra.impex.writeVolume(Gyrus.segmented*255,path+'/testDapyImages/ResultTest/gyrus','.tif')
    print "Interior Volume ", Gyrus.InteriorVolume
    print "Interior Area ", Gyrus.InteriorArea
    print "Gyrus Area ", Gyrus.GyrusArea
    print "Gyrus Volume ", Gyrus.GyrusVolume
    
    print "Comparing the results"
    
    groundInterior=vigra.impex.readVolume(path+'/testDapyImages/ResultTest/Ground_truth/interior00.tif')
    if groundInterior.all()!=Gyrus.res.all(): raise
    
    groundGyrus=vigra.impex.readVolume(path+'/testDapyImages/ResultTest/Ground_truth/gyrus00.tif')
    if groundGyrus.all()!=Gyrus.segmented.all(): raise
    
    print "ok!"
       