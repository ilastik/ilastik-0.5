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
    
    @classmethod
    def __initFromJSon(cls, jsonFile):
        return cls('','',(1,2,3))
        """
        initialFile = ""
    images = ""
    groupNames = []
    sigmaVals = []
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "", ["config_file="])
        for o, a in opts:
            if o in ("--config_file"):
                initialFile = str(a)
    except getopt.GetoptError, err:
        print str(err)
        sys.exit()

    if not initialFile:
        print "no session file provided"
        sys.exit()

    fin = open(initialFile, 'r')
    json_str = fin.read()
    json_input = json.loads(json_str)

    sessionFile = str(json_input.get("session", None))
    if sessionFile is None:
        print "no session file provided"
        sys.exit()

    images = json_input.get("images", None)
    if images is None:
        print "no images provided"
        sys.exit()

    features = json_input.get("features", None)
    if features is None:
        print "no features provided"
        sys.exit()
    
    for feature in features:
        groupNames.append(str(feature[0]))
        sigmaVals.append(float(feature[1]))

    project = projectMgr.Project.loadFromDisk(sessionFile, None)

    # create feature list from options -- use createList as a template
    featureList = featureMgr.ilastikFeatureGroups.createListRestr(groupNames, sigmaVals)
    
    if not featureList:
        print "No features loaded"
        sys.exit()

    baseDir = json_input.get("input_dir", None)
    if baseDir is not None:
        inputPath = str(baseDir) 
    baseDir = json_input.get("output_dir", None)
    if baseDir is not None:
        outputPath = str(baseDir) 

    print "generate features"
    project.dataMgr.module["Classification"]["classificationMgr"].clearFeaturesAndTraining()
    project.dataMgr.Classification.featureMgr = featureMgr.FeatureMgr(project.dataMgr, featureList)
    numberOfJobs = project.dataMgr.Classification.featureMgr.prepareCompute(project.dataMgr)
    project.dataMgr.Classification.featureMgr.triggerCompute()
    project.dataMgr.Classification.featureMgr.joinCompute(project.dataMgr)
    print "generated features"   

    print "generate classifiers"   
    numberOfJobs = 10
    classificationProcess = classificationMgr.ClassifierTrainThread(numberOfJobs, project.dataMgr)
    classificationProcess.start()
    classificationProcess.wait()

    classificationPredict = classificationMgr.ClassifierPredictThread(project.dataMgr)
    classificationPredict.start()
    classificationPredict.wait()
    print "generated classifiers"   
    #time.sleep(10)

    for image in images:
        # run batch process function with filename
        batch = MainBatch(project, image)
        batch.process()
        gc.collect()

    del jobMachine.GLOBAL_WM
        """
    
class BatchProcessCore(object):
    def __init__(self, batchOptions):
        self.batchOptions = batchOptions
        
    def printStuff(self, stuff):
        print stuff
        
    def process(self):
        for i, filename in enumerate(self.batchOptions.fileList):
            filename = str(filename)
            try:
                # input handle
                theDataItem = dataImpex.DataImpex.importDataItem(filename, None)
                
                # output handle           
                fw = h5py.File(str(filename) + '_processed.h5', 'w')
                gw = fw.create_group("volume")
                
                if self.batchOptions.serializeProcessing:
                    mpa = dataMgr.MultiPartDataItemAccessor(theDataItem, 128, 30)

                    for blockNr in range(mpa.getBlockCount()):                       
                        self.printStuff("Part " + str(blockNr) + "/" + str(mpa.getBlockCount()) + " " )
                                                
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
        

