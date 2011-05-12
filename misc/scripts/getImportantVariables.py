#!/usr/bin/python
import h5py
from matplotlib.patches import FancyArrowPatch
from pylab import *
import sys

def getImportantVariables(classFile, nDims, nSel, plotName):
    # dictionary of mapping kernel widths to names 
    kernelDict = {0.3 : 0, 0.7 : 1, 1.0 : 2, 1.6 : 3, 3.5 : 4, 5.0 : 5, 10.0 : 6}
    groupDict = {'Color':0,'Edge':1,'Orientation':2,'Texture':3}
    kernelNames = ['Tiny','Small','Medium','Large','Huge','Megahuge','Gigahuge']
    allGroupNames = ['Color','Edge','Orientation','Texture']
    allGroupAbbrv = ['C','E','O','T']
    kernelAbbrv = ['t','s','m','l','h','M','g']
    abbrv = list()
    for a in allGroupAbbrv:
        for k in kernelAbbrv:
            abbrv.append(a+k)
    fid = h5py.File(classFile,'r')
    gid = fid['features']
    nFeats = len(gid)
    nChannels = zeros((nFeats, ))
    sigmas = zeros((nFeats, ))
    groupNames = list()
    for iFeat in range(nFeats):
        if nDims == 2:
            nChannels[iFeat]=gid["feature_%03d" % iFeat]["number of 2d channels"][...]
        else:
            nChannels[iFeat] = gid['feature_%03d' % iFeat]['number of 3d channels'][...]
        groupNames.append(gid["feature_%03d" % iFeat]["groups"][...])
        sigmas[iFeat] = gid['feature_%03d' % iFeat]["sigma"][...]
    gid = fid['classifiers']
    nRf = len(gid)
    nGroups = len(groupDict)
    nWidths = len(kernelDict)
    varImp = zeros((nRf,nGroups,nWidths))
    for rf in range(nRf):
        featOffset = 0
        varImpMatrix = fid['classifiers/rf_%03d/Variable importance' % rf][:]
        for iFeat in range(nFeats):
            # there are different ways of defining the variable importance, but here we restrict
            # ourselves to the simplest measure, namely the Gini importance
            subImp = varImpMatrix[featOffset:featOffset+nChannels[iFeat],-1]
            # we are interested in the maximum variable importance over all sub-features
            maxChannel = amax(subImp,axis=0)
            varImp[rf, groupDict[groupNames[iFeat]], kernelDict[sigmas[iFeat]]] = max(maxChannel, \
                varImp[rf, groupDict[groupNames[iFeat]], kernelDict[sigmas[iFeat]]])
            featOffset = featOffset + nChannels[iFeat]
    fid.close()
    # extract median
    varImpSorted = sort(varImp, axis=0)
    varImpSorted = varImpSorted[nRf/2,:,:]
    varImpSorted.shape = (nGroups*nWidths, )
    indices = arange(nGroups*nWidths)*1j
    varImpSorted = varImpSorted + indices
    varImpSorted.sort() # the original indices are in the imaginary parts
    indices = imag(varImpSorted).astype('int32')
    varImpSorted = real(varImpSorted)
    if nSel > 0 and nSel < nGroups*nWidths:
        nPrint = nSel
    else:
        nPrint = nGroups*nWidths
    for i in range(nPrint):
        j = i+1
        print "Feature #%02d: %f (%s %s)" % (j, varImpSorted[-j], allGroupNames[indices[-j] / nWidths], \
            kernelNames[indices[-j] % nWidths])
    if plotName != '':
        fig = figure(figsize=(14,6))
        ax2 = axes([0.05,0.05,0.9,0.9])
        varImp.shape = (nRf, nGroups*nWidths)
        boxplot(varImp)
        title('Maximum of mean Gini increases');
        xticks(arange(1,nGroups*nWidths+1), abbrv)
        ymin, ymax = ylim()
        if nSel > 0 and nSel < nGroups*nWidths:
            for iS in range(nSel):
                ax2.add_patch(FancyArrowPatch((indices[-(iS+1)]+1,0.02*ymin+0.98*ymax), \
                (indices[-(iS+1)]+1,0.07*ymin+0.93*ymax),arrowstyle='->',mutation_scale=30,color='blue'))
        savefig(plotName)
        
def printUsage():
    print "Usage: getImportantVariables.py classFile nDims [nSel [plotName]]"
    print "classFile: Name of the file with the exported RF classifiers with variable importance info"
    print "nDims: Number of dimensions of the image data, must be either 2 or 3"
    print "nSel: Number of features to be selected"
    print "plotName: File name of output plot to be created"

#*******************************************************************************
# i f   _ _ n a m e _ _   = =   " _ _ m a i n _ _ "                            *
#*******************************************************************************

if __name__ == '__main__':
    if len(sys.argv) >=2 and sys.argv[1]=='--help':
        printUsage()
        sys.exit(0)
    if len(sys.argv) not in [3,4,5]:
        print "Error: getImportantVariables.py must be called with 2, 3 or 4 input arguments"
        sys.exit(1)
    classFile = sys.argv[1]
    nDims = int(sys.argv[2])
    if nDims not in [2,3]:
        print "Error: number of image dimensions must be 2 or 3"
        sys.exit(1)
    if len(sys.argv)>=4:
        nSel = int(sys.argv[3])
    else:
        nSel = 0
    if len(sys.argv)>=5:
        plotName = sys.argv[4]
    else:
        plotName = ''
    getImportantVariables(classFile,nDims,nSel,plotName)
    sys.exit(0)
