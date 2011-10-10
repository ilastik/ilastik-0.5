

dataFolder='/Users/lfiaschi/phd/workspace/ilastik-github/ilastik/modules/cells_module/core/test_data_batch/'
destFolder='/Users/lfiaschi/Desktop/test'

#File Name to the Gyrus Classifier
fileNameToClassifierGyrus=dataFolder+"classifiers/classifierCh0.h5"
#File Name to the Cells Classifier
fileNameToClassifierCells=dataFolder+"classifiers/classifierCh1.h5"
#File Name to the Dcx Classifier
fileNameToClassifierDcx=dataFolder+"classifiers/classifierCh2.h5"

#The [hysicical dimensions
physSize=(0.757*2,0.757*2,1.0/2.0)


#ACTUAL FUNCTINALITY DO NOT CHANGE
import glob,time
import ilastik
from ilastik.modules.cells_module.core.cellsBatchMgr import *
start=time.time()
"Test the process manager"

fileNames = sorted(glob.glob(dataFolder + "data/*.h5"))

print "THE FILES TO BE PROCESSED ARE: ################################################"
for filename in fileNames:
    print filename
    
print "##########################################################"


print "THE CLASSIFIERS ARE: ################################################"
print fileNameToClassifierGyrus
print fileNameToClassifierDcx
print fileNameToClassifierCells
print "##########################################################"


manager=BatchProcessingManager(fileNames,fileNameToClassifierGyrus,fileNameToClassifierCells,fileNameToClassifierDcx,physSize=physSize,destFolder=destFolder)
manager.Start()

print "Total batch process time " + str(time.time()-start)


