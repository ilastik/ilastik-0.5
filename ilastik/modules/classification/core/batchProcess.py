import os
import sys
import numpy                                                    
import re                                                       
import ilastik.modules
ilastik.modules.loadModuleCores()
from ilastik.core import dataMgr

from ilastik.modules.classification.core.classificationMgr import ClassificationModuleMgr
from ilastik.modules.classification.core.featureMgr import FeatureMgr

from ilastik.modules.classification.core import classificationMgr
from ilastik.core import dataImpex
from ilastik.core.volume import DataAccessor                    

import traceback
import getopt
import h5py
import errno
import gc
import json
from ilastik.core import loadOptionsMgr
from ilastik.core import jobMachine
from ilastik.core.dataImpex import DataImpex



inputPath=""
outputPath=""

#*******************************************************************************
# M a i n B a t c h                                                            *
#*******************************************************************************

class MainBatch():
    def __init__(self, project, json_input):
        grp = None
        self.dataMgr = dataMgr.DataMgr(grp)
        self.project = project
        self.options = loadOptionsMgr.loadOptions()
        self.options.channels = []
        self.options.channels.append(0)
        self.json_input = json_input
        self.fileBase = json_input.get("name", None)

    def process(self):
        #put provided image in the hdf5
        try:
            slices = self.json_input.get("slices", None)
            fileList = []
            fileListChannel = []
            fileList.append(fileListChannel)
            sizez = 1
            if slices is None:
                fileList[0].append(str(inputPath + str(self.fileBase)))
            else:
                [minz, maxz] = slices
                sizez = maxz - minz + 1
                for sliceiter in range(minz, maxz+1):
                    filename = self.fileBase % sliceiter
                    fileList[0].append(str(inputPath + filename))

            shape = dataImpex.DataImpex.readShape(fileList[0][0])
            self.options.shape = (shape[0], shape[1], sizez)

            if sizez is 1:
                theDataItem = dataImpex.DataImpex.importDataItem(fileList[0][0], None)
                if theDataItem is None:
                    print "No _data item loaded"
                    return
                self.dataMgr.append(theDataItem, True)
            else: 
                theDataItem = dataImpex.DataImpex.importDataItem(fileList, self.options)
                if theDataItem is None:
                    print "No _data item loaded"
                    return
                self.dataMgr.append(theDataItem, True)
                self.dataMgr._dataItemsLoaded[-1] = True

                theDataItem._hasLabels = True
                theDataItem._isTraining = True
                theDataItem._isTesting = True


            #print "generate features image"   
                    
            fm = self.dataMgr.Classification.featureMgr      
            fm.setFeatureItems(self.project.dataMgr.Classification.featureMgr.featureItems)
    
            fm.prepareCompute(self.dataMgr)
            fm.triggerCompute()
            fm.joinCompute(self.dataMgr)
            #print "generated features image"   

            self.dataMgr.module["Classification"]["classificationMgr"].classifiers = \
                self.project.dataMgr.module["Classification"]["classificationMgr"].classifiers
            self.dataMgr.module["Classification"]["labelDescriptions"] = \
                self.project.dataMgr.module["Classification"]["labelDescriptions"]

            #print "generate classifiers image"   
            classificationPredict = classificationMgr.ClassifierPredictThread(self.dataMgr)
            classificationPredict.start()
            classificationPredict.wait()
            classificationPredict.generateOverlays()
            #print "generated classifiers image"   

            #save results
            try:
                if outputPath is not None:
                    os.makedirs(os.path.dirname(outputPath))
            except OSError as exc:
                if exc.errno == errno.EEXIST:
                    pass
                else:
                    raise

            outName = self.json_input.get("output", None)
            if outName is None:
                outName = fileList[0][0] + '.h5'
           
            outName = outputPath + outName

            f = h5py.File(outName, 'w')
            g = f.create_group("volume")
            self.dataMgr[0].serialize(g)
            f.close()

            print "finished processing image: %s" % (outName)
             
        except Exception, e:
            print "######Exception"
            traceback.print_exc(file=sys.stdout)
            print e
            
            
            
#*******************************************************************************
# B a t c h O p t i o n s                                                      *
#*******************************************************************************

class BatchOptions(object):
    def __init__(self, outputDir, classifierFile, fileList, labelDescriptions=None):
        self.outputDir = outputDir
        self.classifierFile = classifierFile
        self.fileList = fileList
        self.labelDescriptions = labelDescriptions
        
        self.writePrediction = True
        self.writeFeatures = False
        self.writeSegmentation = True
        self.writeUncertainty = True                           
        self.writeSourceData = True                             
        self.writeHDF5 = True
        self.writeImages = False
        self.tiledProcessing = False
        self.pngResults = True
        self.h5Results = True
        
        # Export to raw byte arrays 
        # by Daniel Alievsky (Smart Imaging Technologies)
        self.rawSources = False                                 
        self.rawSourceDimX = -1                                 
        self.rawSourceDimY = -1                                 
        self.rawSourceDataType = "byte"                         
        self.rawCastRawSourceToFloat = False                       
        self.rawResults = False     
                                    
        # Customized tile sizes
        # by Daniel Alievsky (Smart Imaging Technologies)
        self.tileDim = 128                                      
        self.tileOverlap = 30                                   
        
        self.featureList = None
        self.classifiers = None
        
        self.isReady = False
        
    def setFeaturesAndClassifier(self, classifiers=None, featureList=None):
        # get Classifers
        if classifiers is None:
            self.classifiers = ClassificationModuleMgr.importClassifiers(self.classifierFile)
        else:
            self.classifiers = classifiers
            
        if featureList is None:
            self.featureList = FeatureMgr.loadFeatureItemsFromFile(self.classifierFile)
        else:
            self.featureList = featureList
        
        self.isReady = True
    
    @staticmethod
    def initFromJSon(jsonFile=None):
        if not jsonFile:
            raise RuntimeError("initFromJSon(): No json file provided")
    
        fin = open(jsonFile, 'r')
        json_str = fin.read()
        json_input = json.loads(json_str)
    
        classifierFile = str(json_input.get("session", None))
        if classifierFile is None:
            raise RuntimeError("initFromJSon(): No classifier provided in json file")
    
        images = json_input.get("images", None)
        if images is None:
            raise RuntimeError("initFromJSon(): No images provided in json file")
        fileList = []
        for image in images:
            fileList.append(str(image.get("name", None)))
    
            
        outputDir = json_input.get("output_dir", None)
        if outputDir is not None:
            outputDir = str(outputDir)
            # try to create outputDir
            try:
                if not os.path.exists(outputDir):
                    os.mkdir(outputDir)
            except:
                raise IOError("The output directory %s can not be created, aborting." % outputDir)
                    
            
        bo = BatchOptions(outputDir, classifierFile, fileList)
        bo.tiledProcessing = bool(json_input.get("tiledProcessing", False))          

        options = json_input.get("options", None);                                      
        if options is not None:                                                         
            bo.writeSourceData = bool(options.get("writeSourceData", True))             
            bo.writePrediction = bool(options.get("writePrediction", True))             
            bo.writeSegmentation = bool(options.get("writeSegmentation", True))         
            bo.writeUncertainty = bool(options.get("writeUncertainty", True))    
            bo.pngResults = bool(options.get("pngResults", False))                      
            bo.h5Results = bool(options.get("h5Results", True))  
                 
            # Export to raw byte arrays 
            # by Daniel Alievsky (Smart Imaging Technologies)
            bo.rawResults = bool(options.get("rawResults", False))                                             
            bo.rawSources = bool(options.get("rawSources", False))                      
            bo.rawSourceDimX = long(options.get("rawSourceDimX", -1))                   
            bo.rawSourceDimY = long(options.get("rawSourceDimY", -1))                   
            bo.rawSourceDataType = str(options.get("rawSourceDataType", "byte"))        
            bo.rawCastRawSourceToFloat = bool(options.get("rawCastRawSourceToFloat", False))   
            
            # Customized tile sizes
            # by Daniel Alievsky (Smart Imaging Technologies)
            bo.tileDim = long(options.get("tileDim", bo.tileDim))                       
            bo.tileOverlap = long(options.get("tileOverlap", bo.tileOverlap))      

        return bo


#*******************************************************************************
# B a t c h P r o c e s s C o r e                                              *
#*******************************************************************************

class BatchProcessCore(object):
    def __init__(self, batchOptions):
        self.batchOptions = batchOptions
        
    def printStuff(self, stuff):
        print stuff
        
    def _writeSegmentationToDisk(self, data, baseFilename):
        if self.batchOptions.pngResults:
            fn = "".join((baseFilename, "_segmentation"))
            DataImpex.exportToStack(fn, 'png', data)
            
        # Export to raw byte arrays 
        # by Daniel Alievsky (Smart Imaging Technologies) 
        if self.batchOptions.rawResults:
            fn = "".join((baseFilename, "_segmentation.raw"))
            print "Writing raw segmentation (",str(data.dtype),") into",fn
            data.tofile(fn)
                     
    def _writeUncertaintyToDisk(self, data, baseFilename):
        if self.batchOptions.pngResults:
            fn = "".join((baseFilename, "_uncertainty"))
            DataImpex.exportToStack(fn, 'png', data)
            
        # Export to raw byte arrays 
        # by Daniel Alievsky (Smart Imaging Technologies) 
        if self.batchOptions.rawResults:
            fn = "".join((baseFilename, "_uncertainty.raw"))
            print "Writing raw segmentation (", str(data.dtype), ") into" , fn
            data.tofile(fn)
               
    def _writePredictionToDisk(self, data, baseFilename, classLabel, predictionName):   
        if self.batchOptions.pngResults:
            fn = "_".join((baseFilename, predictionName))
            DataImpex.exportToStack(fn, 'png', data)
            
        # Export to raw byte arrays 
        # by Daniel Alievsky (Smart Imaging Technologies) 
        if self.batchOptions.rawResults:
            fn = "".join((baseFilename, "_prediction_%03d.raw" % classLabel))
            print "Writing raw segmentation (", str(data.dtype), ") into ", fn
            data.tofile(fn)
        
    def _writeFeaturesToDisk(self, image, baseFilename):
        """
        to be implemented
        """
        

    def process(self):
        for filename in self.batchOptions.fileList:
            try:
                bo = self.batchOptions  
                                         
                # input handle
                theDataItem = self.readSource(filename)  
                
                # Support for working with raw byte arrays
                # added by Daniel Alievsky (Smart Imaging Technologies)     
                if bo.rawSources:                                                       
                    p = re.compile("%BAND%")                                            
                    filename = p.sub("bands", filename) # more readable file name       

                # output handle     
                filen = os.path.split(filename)[1] 
                fw = None                                                               
                gw = None                                                               
                
                # Tiled processing mode
                # note that: exporting results to PNG or Raw does not work in that mode
                if bo.tiledProcessing:                           
                    self.printStuff(" Starting with tiling...")                         
                    if bo.rawResults:                                                   
                        raise IOError("Tiled processing with raw serialization is not implemented yet: please set options.rawResults to false") 
                    fw = h5py.File(bo.outputDir + '/' + filen + '_processed.h5', 'w')   
                    gw = fw.create_group("volume")                                      
                    mpa = dataMgr.MultiPartDataItemAccessor(theDataItem, bo.tileDim, bo.tileOverlap)  

                    for blockNr in range(mpa.getBlockCount()):                       

                        yield "Block " + str(blockNr +1 ) + "/" + str(mpa.getBlockCount())
                        print "Block " + str(blockNr +1 ) + "/" + str(mpa.getBlockCount())             
                        dm = dataMgr.DataMgr()
                                        
                        di = mpa.getDataItem(blockNr)
                        dm.append(di, alreadyLoaded=True)
                                  
                        fm = dm.Classification.featureMgr      
                        fm.setFeatureItems(bo.featureList)                              

                        fm.prepareCompute(dm)
                        fm.triggerCompute()
                        fm.joinCompute(dm)
        
                        dm.module["Classification"]["classificationMgr"].classifiers = bo.classifiers  
                        if bo.labelDescriptions is not None:                                           
                            dm.module["Classification"]["labelDescriptions"] = bo.labelDescriptions   

                        self.printStuff(" Starting classifier (serializing)...\n")      
                        classificationPredict = classificationMgr.ClassifierPredictThread(dm)
                        classificationPredict.start()
                        classificationPredict.wait()
                                                
                        self.printStuff(" Generating overlays...\n")                    
                        classificationPredict.generateOverlays(makePrediction=bo.writePrediction, makeSegmentation=bo.writeSegmentation, makeUncertainty=bo.writeUncertainty)  

                        self.writeResultToDisk(dm, gw, filen)                      
                        self.printStuff(" done\n")                                      
                    
                    del fm
                    del dm
                    gc.collect()
                     
                # Non tiled processing mode
                else:
                    self.printStuff(" Starting...")                                     
                                                     
                    dm = dataMgr.DataMgr()
                    dm.append(theDataItem, True)                    

                    self.printStuff(" Features...")                                     
                    fm = dm.Classification.featureMgr
                    fm.setFeatureItems(bo.featureList)                                 
    
                    self.printStuff(" Preparing...")                                    
                    fm.prepareCompute(dm)
                    fm.triggerCompute()
                    fm.joinCompute(dm)
    
                    dm.module["Classification"]["classificationMgr"].classifiers = bo.classifiers  
                    if bo.labelDescriptions is not None:                                           
                        dm.module["Classification"]["labelDescriptions"] = bo.labelDescriptions   
    
                    self.printStuff(" Starting classifier (not serializing)...")        
                    classificationPredict = classificationMgr.ClassifierPredictThread(dm)
                    classificationPredict.start()
                    classificationPredict.wait()
                    
                    self.printStuff(" Generating overlays...")                          
                    classificationPredict.generateOverlays(makePrediction=True, makeSegmentation=True, makeUncertainty=True)  
                    
                    if bo.h5Results:                                               
                        fw = h5py.File(bo.outputDir + '/' + filen + '_processed.h5', 'w') 
                        gw = fw.create_group("volume") 
                    self.writeResultToDisk(dm, gw, filen)     
                    self.printStuff(" done\n")                                          
                    
                    del fm
                    del dm
                    gc.collect()

                if not fw == None:                                                      
                    fw.close()
                    
            except Exception, e:
                print "Error: BatchProcessCore.proces() "
                traceback.print_exc(file=sys.stdout)
                print e

            yield filename
            
    def _readRawSource(self, fileName):
        """ """
        dimX = self.batchOptions.rawSourceDimX
        dimY = self.batchOptions.rawSourceDimY
        if dimX <= 0 or dimY <= 0:
            raise IOError("In rawSources mode, config_file must contain positive rawSourceDimX and rawSourceDimY values")
        if self.batchOptions.rawSourceDataType == "byte":
            srcType = numpy.uint8
        elif self.batchOptions.rawSourceDataType == "short":
            srcType = numpy.uint16
        elif self.batchOptions.rawSourceDataType == "int":
            srcType = numpy.int32
        elif self.batchOptions.rawSourceDataType == "long":
            srcType = numpy.int64
        elif self.batchOptions.rawSourceDataType == "float":
            srcType = numpy.float32
        elif self.batchOptions.rawSourceDataType == "double":
            srcType = numpy.float64
        else:
            raise IOError("Unknown rawSourceDataType=" + str(self.batchOptions.rawSourceDataType))
        self.printStuff(" Reading raw RGB data " + str(fileName) + " (" + str(dimX) + "x" + str(dimY) + "x" + str(srcType) + ")...")
        p = re.compile("%BAND%")
        npr = numpy.fromfile(p.sub("r", fileName), srcType, dimX * dimY)
        npg = numpy.fromfile(p.sub("g", fileName), srcType, dimX * dimY)
        npb = numpy.fromfile(p.sub("b", fileName), srcType, dimX * dimY)
        data = numpy.empty(shape=(1, 1, dimY, dimX, 3), dtype=srcType)
        data[:,:,:,:,0] = npr.reshape((1, 1, dimY, dimX))
        data[:,:,:,:,1] = npg.reshape((1, 1, dimY, dimX))
        data[:,:,:,:,2] = npb.reshape((1, 1, dimY, dimX))
        if self.batchOptions.rawCastRawSourceToFloat and srcType != numpy.float32:
            # Don't sure, is it really necessary, but reading PNG/JPEG/GIF leads to float32 arrays
            self.printStuff(" Casting raw data to numpy.float32")
            data = data.astype(numpy.float32)
        theDataItem = dataMgr.DataItemImage(fileName)
        dataAcc = DataAccessor(data)
        theDataItem._dataVol = dataAcc
        return theDataItem
        

    def readSource(self, fileName):     
        self.printStuff(" Reading image " + str(fileName) + "...")                                         
        
        if self.batchOptions.rawSources:
            return self._readRawSource(fileName)
        else:
            theDataItem = dataImpex.DataImpex.importDataItem(fileName, None)
        
        return theDataItem

    def writeResultToDisk(self, dataMgr, hdfGroup, fileName):                            
        self.printStuff(" Serialization of " + str(dataMgr[0]) + "...")
        
        # write h5 output for non-tiled and tiled mode 
        if self.batchOptions.h5Results:
            dataItemImage = dataMgr[0]
            if not self.batchOptions.tiledProcessing:
                dataItemImage.serialize(hdfGroup)
            else:
                destbegin = (0,0,0)
                destend = (0,0,0)
                srcbegin = (0,0,0)
                srcend = (0,0,0)
                destshape = (0,0,0)
                if dataItemImage._writeEnd != (0,0,0): # used in tiling mode (self.batchOptions.tiledProcessing)
                    destbegin = dataItemImage._writeBegin
                    destend = dataItemImage._writeEnd
                    srcbegin = dataItemImage._readBegin
                    srcend = dataItemImage._readEnd
                    destshape = dataItemImage._writeShape
                dataItemImage.module['Classification'].serializeCustom(hdfGroup, destbegin, destend, srcbegin, srcend, destshape, writeLabels=False)

        # tiled processing only supports h5        
        if self.batchOptions.tiledProcessing:
            if self.batchOptions.rawResults or self.batchOptions.pngResults:
                self.printStuff('Warning: Can not write PNG or RAW files in tiled processing mode! Only h5 results can be exported...')
            return
        
        baseFileName = os.path.splitext(fileName)[0]
        baseFileName = os.path.join(self.batchOptions.outputDir, "".join((baseFileName, "_processed")))
        image = dataMgr[0].module['Classification'].dataItemImage
        
        # write segmentation
        if self.batchOptions.writeSegmentation:
            if image.overlayMgr["Classification/Segmentation"] is not None:
                seg = image.overlayMgr["Classification/Segmentation"][:,:,:,:,:].astype(numpy.uint8)
                self._writeSegmentationToDisk(seg, baseFileName)
                
        # write uncertainty
        if self.batchOptions.writeUncertainty:
            if image.overlayMgr["Classification/Uncertainty"] is not None:
                unc = image.overlayMgr["Classification/Uncertainty"][:,:,:,:,:]*255
                self._writeUncertaintyToDisk(unc, baseFileName)
         
        # write prediction       
        
        descriptions = dataMgr.module["Classification"]["labelDescriptions"]
        if descriptions is not None and len(descriptions) > 0:
            for k, d in enumerate(descriptions):
                if image.overlayMgr["Classification/Prediction/" + d.name] is not None:
                    pred = image.overlayMgr["Classification/Prediction/" + d.name][:,:,:,:,0]
                    if self.batchOptions.writePrediction:
                        self._writePredictionToDisk(pred, baseFileName, k, d.name)

            



#*******************************************************************************
# i f   _ _ n a m e _ _   = =   " _ _ m a i n _ _ "                            *
#*******************************************************************************

if __name__ == "__main__": 
    if len(sys.argv) == 1:
        print """ Usage: --config_file=<json-file>
                  
                  The json file should look like this:
                  
                {
                    "output_dir" : "<abs path output dir>",
                    "session" : "<abs path to your classifier or project file>",
                    "images" : [
                        { "name" : "<abs path to your file1>"},
                        { "name" : "<abs path to your file1>"}
                    ]
                }
                """
        sys.exit()
        
                
      
    try:
        opts, args = getopt.getopt(sys.argv[1:], "", ["config_file="])
        print opts
        print args
        if len(opts) == 0:
            raise(IOError("Usage: --config_file=<json-file>"))
            
        o, a = opts[0]
        if o != "--config_file":
            raise(IOError("Usage: --config_file=<json-file>"))
        else:
            jsonFile = str(a)

    except getopt.GetoptError, err:
        raise(IOError(err))
        sys.exit()
        
    batchOptions = BatchOptions.initFromJSon(jsonFile)
    batchOptions.setFeaturesAndClassifier()
    batchProcess = BatchProcessCore(batchOptions)
    for i in batchProcess.process():
        print "Processed " + str(i) + "\n"                                              
    
    del jobMachine.GLOBAL_WM
    
    
    
    
        

