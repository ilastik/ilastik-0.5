import os
import sys
import ilastik.modules
ilastik.modules.loadModuleCores()
from ilastik.core.volume import DataAccessor
from ilastik.core import dataMgr

from ilastik.modules.classification.core.classificationMgr import ClassificationModuleMgr
from ilastik.modules.classification.core.featureMgr import FeatureMgr

from ilastik.modules.classification.core import classificationMgr
from ilastik.core import dataImpex
from ilastik.core import jobMachine

import traceback
import getopt
import h5py
import fileinput
import errno
import gc
import json
from ilastik.gui import loadOptions



inputPath=""
outputPath=""

class MainBatch():
    def __init__(self, project, json_input):
        grp = None
        self.dataMgr = dataMgr.DataMgr(grp)
        self.project = project
        self.options = loadOptions.loadOptions()
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

            self.dataMgr.module["Classification"]["classificationMgr"].classifiers = self.project.dataMgr.module["Classification"]["classificationMgr"].classifiers
            self.dataMgr.module["Classification"]["labelDescriptions"] = self.project.dataMgr.module["Classification"]["labelDescriptions"]

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
            
            
            
class BatchOptions(object):
    def __init__(self, outputDir, classifierFile, fileList):
        self.outputDir = outputDir
        self.classifierFile = classifierFile
        self.fileList = fileList
        
        self.writePrediction = True
        self.writeFeatures = False
        self.writeSegmentation = False
        self.writeHDF5 = True
        self.writeImages = False
        self.serializeProcessing = True
        
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
            
        return BatchOptions(outputDir, classifierFile, fileList)

    

    
class BatchProcessCore(object):
    def __init__(self, batchOptions):
        self.batchOptions = batchOptions
        
    def printStuff(self, stuff):
        print stuff
        
    def writeSegmentationToDish(self):
        """
        to be implemented
        take care that also single files and/or hdf5 output should be supported
        """
        
    def writeFeaturesToDish(self):
        """
        to be implemented
        """
        
    def writePredictionToDish(self):
        """
        to be implemented
        """
        
    def process(self):
        for i, filename in enumerate(self.batchOptions.fileList):
            try:
                # input handle
                
                theDataItem = dataImpex.DataImpex.importDataItem(filename, None)
                
                # output handle           
                fw = h5py.File(str(filename) + '_processed.h5', 'w')
                gw = fw.create_group("volume")
                
                if self.batchOptions.serializeProcessing:
                    mpa = dataMgr.MultiPartDataItemAccessor(theDataItem, 128, 30)

                    for blockNr in range(mpa.getBlockCount()):                       

                        yield "Block " + str(blockNr +1 ) + "/" + str(mpa.getBlockCount())                        
                        dm = dataMgr.DataMgr()
                                        
                        di = mpa.getDataItem(blockNr)
                        dm.append(di, alreadyLoaded = True)
                                  
                        fm = dm.Classification.featureMgr      
                        fm.setFeatureItems(self.batchOptions.featureList)
                        
        
                        fm.prepareCompute(dm)
                        fm.triggerCompute()
                        fm.joinCompute(dm)
        
                        dm.module["Classification"]["classificationMgr"].classifiers = self.batchOptions.classifiers
                        
                        classificationPredict = classificationMgr.ClassifierPredictThread(dm)
                        classificationPredict.start()
                        classificationPredict.wait()

                        dm[0].serialize(gw)
                        self.printStuff(" done\n")
                        
                        del fm
                        del dm
                        gc.collect()
                     
                else: # non serialized
                    dm = dataMgr.DataMgr()
                    dm.append(theDataItem, True)                    
    
                    fm = dm.Classification.featureMgr      
                    fm.setFeatureItems(self.batchOptions.featureList)
    
                    fm.prepareCompute(dm)
                    fm.triggerCompute()
                    fm.joinCompute(dm)
    
                    dm.module["Classification"]["classificationMgr"].classifiers = self.batchOptions.classifiers
    
                    classificationPredict = classificationMgr.ClassifierPredictThread(dm)
                    classificationPredict.start()
                    classificationPredict.wait()
                    
                    dm[0].serialize(gw)
                    self.printStuff(" done\n")
                    
                    del fm
                    del dm
                    gc.collect()

                fw.close()
                    
            except Exception, e:
                print "Error: BatchProcessCore.proces() "
                traceback.print_exc(file=sys.stdout)
                print e

            yield filename

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
        print "Processing " + str(i) + "\n"
    
    del jobMachine.GLOBAL_WM
    
    
    
    
        

