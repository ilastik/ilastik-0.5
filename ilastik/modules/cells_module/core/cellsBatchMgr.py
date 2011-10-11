# -*- coding: utf-8 -*-
import vigra
import numpy
import h5py
import csv
try:
  import jpype
except:
    print "Jpype is not there"
import sys
import gc




from PyQt4 import QtGui, QtCore

import os






#from ilastik.modules.cells_module.core.lifReader import readLif
from channelsjobs.cellsMgrBrdU import BrdUSegmentation 
from channelsjobs.cellsMgrDapy import GyrusSegmentation
from channelsjobs.cellsMgrDcX import DcxSegmentation

from exporterImagesToFolders import exporterToIm



class process_series(object):
    """This class process a single series"""
    
    def __init__(self,fileName,fileNameToClassifierGyrus,fileNameToClassifierCells,fileNameToClassifierDcx,SerieID,Serie,physSize=(1,1,1),destFolder=None):  
        
        
        self.destFolder=destFolder
        self.physSize=physSize
        print "PhysSize", self.physSize
        self.voxelVol=physSize[0]*physSize[1]*physSize[2]
        self.currentfileName=fileName
        
        #Create the list of data series
        base, ext = os.path.splitext(self.currentfileName)
        folder,file=os.path.split(base)
        
            
        self.filenametoclassifierGyrus=fileNameToClassifierGyrus
        self.filenametoclassifierCells=fileNameToClassifierCells
        self.fileNameToClassifierDcx=fileNameToClassifierDcx
        self.serieid=SerieID
        
        if self.destFolder==None:
            self.dirResultsImages=base + "_result_series" + str(self.serieid)
            self.fileResultsName= base + "_result_series" + str(self.serieid) +".csv"
            self.fileDistanceMatrixName=base + "_result_series" + str(self.serieid)+ "DM" +".csv"
        else:
            self.dirResultsImages=destFolder+"/"+ file + "_result_series" + str(self.serieid)
            self.fileResultsName= destFolder+"/"+ file + "_result_series" + str(self.serieid) +".csv"
            self.fileDistanceMatrixName=destFolder+"/"+ file + "_result_series" + str(self.serieid)+ "_DM" +".csv"
        
        self.setData(Serie) 
        
        
    def process(self):               
        
        print "Segmenting the Dapy Channel"
        #print self.DapyChannel.shape
        #print self.DapyChannel.dtype
        self.Gyrus=GyrusSegmentation(self.DapyChannel,filenametoclassifier=self.filenametoclassifierGyrus,physicalSize=self.physSize)
        
        print "Segmenting the BrdU channel"
        self.Cells=BrdUSegmentation(self.BrdUChannel,self.filenametoclassifierCells,self.Gyrus.res+self.Gyrus.segmented,physicalSize=self.physSize)
             
        print "Congratulations! You have Detected " + str(len(self.Cells.DictPositions)) + " cells"
        
        
        print "Gathering informations Dcx channel"
        self.Dcx=DcxSegmentation(self.Cells.DictPositions,self.DcxChannel,self.fileNameToClassifierDcx)
        
        

        print "Exporting the result to file: " + self.fileResultsName
        self.ExportResults()
        
        print "Processed file: " + self.currentfileName
        print "Saving the images to the folder: " + self.dirResultsImages
        self.ExportImages()
        
    
    def setData(self,Serie,RF=2):
        print "The series that is being processed has a shape :", Serie.shape

        self.DapyChannel = Serie[0, :, :, :, 0].view(numpy.ndarray).astype(numpy.float32)
        self.BrdUChannel = Serie[0, :, :, :, 1].view(numpy.ndarray).astype(numpy.float32)
        self.DcxChannel =  Serie[0, :, :, :, 2].view(numpy.ndarray).astype(numpy.float32)
        
    
    def ExportResults(self):
        self._exportChannelsResults()
        self._exportDistanceMatrix()
        
        
    
    def _exportDistanceMatrix(self):
        
        DM=self.Cells.distanceMatrix
        
        numpy.savetxt(self.fileDistanceMatrixName,DM,fmt='%3.3f')

        
    def _exportChannelsResults(self):
        
        f=open(self.fileResultsName,'wb')
        
        self.Header=['File Name','Data Series N',
		             'Used Classifier Gyrus', 'Used Classifier Cells', 'Used Classifier Dcx',  
                     
                     'cell id','Z_center','Distance from Interior','Cell Volume',
                     'Cell Average BrdU Intensity','Cell Average Dcx Intensity', 'Positive to Dcx',
                     'Gyrus Volume =' + str(self.Gyrus.GyrusVolume) ,'Gyrus Area',
                     "Interior Volume= " + str(self.Gyrus.InteriorVolume), "Interior Area",
                     'AI Slice in Dapy channel','AI Slice in BrdU channel','AI Slice in Dcx channel']
        
        try:
            writer = csv.writer(f,delimiter=',')
            writer.writerow(self.Header)
            for k in self.Cells.DictCenters.iterkeys():
                x=self.Cells.DictCenters[k][0]
                y=self.Cells.DictCenters[k][1]
                z=self.Cells.DictCenters[k][2]
                #print self.Dcx.dictPositiveCells
                #print self.Dcx.DictIntDcX
                row =[self.currentfileName,self.serieid,
		              
                      self.filenametoclassifierGyrus, self.filenametoclassifierCells,  self.fileNameToClassifierDcx,
                      
                      k, z, self.Gyrus.distanceTransformed[x][y][z],   len(self.Cells.DictPositions[k][0])*self.voxelVol,
                      self.Cells.DictIntBrdU[k],self.Dcx.DictIntDcX[k],self.Dcx.dictPositiveCells[k],
                      self.Gyrus.GyrusVolume,self.Gyrus.GyrusArea[z],
                      self.Gyrus.InteriorVolume,self.Gyrus.InteriorArea[z],
                      self.Gyrus.averageIntSlice[z],self.Cells.averageIntSlice[z],self.Dcx.averageIntSlice[z]]
                writer.writerow(row)
        finally:
            f.close()
            
        

    def ExportImages(self):

        #self.pickleStuff(self.Cells.DictCenters,"dict-centers")
        #self.pickleStuff(self.Cells.DictPositions,"dict-centers")
        #self.pickleStuff(self.Cells,'Cells')
        #self.pickleStuff(self.Gyrus,'Gyrus')
        #self.pickleStuff(self.Dcx, 'Dcx')
        #self.pickleStuff(self.BrdUChannel, 'BrdU_ch')
        #self.pickleStuff(self.DcxChannel, 'Dcx_ch')
        #self.pickleStuff(self.DapyChannel,'Dapy_ch')
        #self.pickleStuff(self.Gyrus.segmented, "segmentedgyrus")
        
        exporter=exporterToIm(self.dirResultsImages,self.Gyrus,self.DapyChannel,self.Cells,self.BrdUChannel,self.Dcx,self.DcxChannel)
        exporter.export()
    
    def pickleStuff(self,obj,name):
        import pickle
        print "pickling " + name
        output = open(self.dirResultsImages+name+'.pkl', 'wb')
        pickle.dump(obj,output)
        output.close()


class BatchProcessingManager(object):
    def __init__(self,fileNameList,fileNameToClassifierGyrus,fileNameToClassifierCells, fileNameToClassifierDcx,physSize=(1,1,1),destFolder=None):
        "set the options for the current batch process"
        
        self.destFolder=destFolder
        self.physSize=physSize
        self.voxelVol=physSize[0]*physSize[1]*physSize[2]
        print "Physical Size of the files ..... ... .. . . . ..", self.physSize
        
     
        
        if not os.path.exists(destFolder) and self.destFolder != None:  os.mkdir(destFolder)
        
        self.fileNamesList=fileNameList
        self.fileNameToClassifierGyrus=fileNameToClassifierGyrus
        self.fileNameToClassifierCells=fileNameToClassifierCells
        self.fileNameToClassifierDcx=fileNameToClassifierDcx
        
        self.currentFileName=None
        self.listSeries=[]
        
    def Start(self):
        for currentfileName in self.fileNamesList:
            self.currentfileName=str(currentfileName)            
            #Create the list of data series
            base, ext = os.path.splitext(self.currentfileName)
            if ext==".h5":
                self.processHDF5File(self.currentfileName)
            else:
                raise RuntimeError("Unrecognized file format " + ext)
            
            print "Start processing file: " + str(self.currentfileName)     
            self.processListSeries(self.currentfileName)
            
    
    def processListSeries(self,fileName):    
        for seriesID in range(len(self.listSeries)): 
            print "From : " + self.currentfileName + " Processing Series " + str(seriesID) 
            

            PS=process_series(self.currentfileName,self.fileNameToClassifierGyrus,self.fileNameToClassifierCells,self.fileNameToClassifierDcx,seriesID,self.listSeries[seriesID],self.physSize,self.destFolder)                    
            PS.process()
            
            #try to call the garbage collector
            del PS
            gc.collect()
            
            
        
        self.listSeries=[]
        gc.collect()
               
    def processHDF5File(self,fileName):
        print "Loading File: " + fileName
        try:
            hf=h5py.File(fileName, 'r')
        except Exception,e:
            print e
            raise RuntimeError("Unable to load the file: "   + fileName)
        
        
        
        if ('metadata' in hf.keys()):
            if ('units' in hf['metadata'].keys()):
                a=hf['metadata/units']
                self.physSize=(a[0][0],a[1][0],a[2][0])
                print "Phys Size into the file: ", self.physSize
        
        self.listSeries.append(hf['volume/data'].value)
        hf.close() 
         

        

        
            
    


def Run():
    fileNameToClassifier=sys.argv[1]
    fileNames=sys.argv[2:]
    
    manager=BatchProcessingManager(fileNames,fileNameToClassifier)
    manager.Start()
        
################################TEST#################################





    

if __name__ == "__main__":
    import glob,time
    start=time.time()
    "Test the process manager"
    testFolder='/Users/lfiaschi/phd/workspace/ilastik-github/ilastik/modules/cells_module/core/test_data_batch'
    
    fileNames = sorted(glob.glob(testFolder + "/data/*.h5"))
    
    
    physSize=(0.757*2,0.757*2,1.0/2.0)
    
    fileNameToClassifierGyrus=testFolder+"/classifiers/classifierCh0.h5"
    fileNameToClassifierCells=testFolder+"/classifiers/classifierCh1.h5"
    fileNameToClassifierDcx=testFolder+"/classifiers/classifierCh2.h5"
    
    print fileNames
    
    manager=BatchProcessingManager(fileNames,fileNameToClassifierGyrus,fileNameToClassifierCells,fileNameToClassifierDcx,physSize=physSize,destFolder=testFolder+"/results")
    manager.Start()
    
    print "Total batch process time " + str(time.time()-start)




