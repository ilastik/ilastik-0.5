
#Remember to put / at the end of the path
dataFolder='/home/lfiaschi/Data/ana-martin/desiree/NesCreERT2Dkk_4weeks/clustered/cluster0/'
#Here you don't need
destFolder=dataFolder+'results'

#File Name to the Gyrus Classifier
fileNameToClassifierGyrus=dataFolder+"classifiers/classifier_ch0.h5"
#File Name to the Cells Classifier
fileNameToClassifierCells=dataFolder+"classifiers/classifier_ch1.h5"
#File Name to the Dcx Classifier
fileNameToClassifierDcx=dataFolder+"classifiers/classifier_ch2.h5"

#The  dimensions are taken directly from the files if not specified
#physSize=(0.757*2,0.757*2,1.0/2.0)


#ACTUAL FUNCTINALITY DO NOT CHANGE
import glob,time
import ilastik
from ilastik.modules.cells_module.core.cellsBatchMgr import *
start=time.time()
"Test the process manager"

fileNames = sorted(glob.glob(dataFolder + "*.h5"))

print "THE FILES TO BE PROCESSED ARE: ################################################"
for filename in fileNames:
    print filename
    
print "##########################################################"


print "THE CLASSIFIERS ARE: ################################################"
print fileNameToClassifierGyrus
print fileNameToClassifierDcx
print fileNameToClassifierCells
print "##########################################################"


manager=BatchProcessingManager(fileNames,fileNameToClassifierGyrus,fileNameToClassifierCells,fileNameToClassifierDcx,destFolder=destFolder)
manager.Start()

print "Total batch process time " + str(time.time()-start)


