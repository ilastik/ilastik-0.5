import numpy

try:
    from vigra import vigranumpycmodule as vm
except:
    try:
        import vigranumpycmodule as vm
    except:
        pass
    
class FeatureMgr():
    def __init__(self, featureItems=[]):
        self.featureItems = featureItems
        
    def setFeatureItems(self, featureItems):
        self.featureItems = featureItems
        
    def triggerCompute(self, dataMgr):
        for dataIndex in xrange(0,len(dataMgr)):
            
            # data will be loaded if not
            data = dataMgr[dataIndex]
            print '\nData Item %s: ' % data.fileName
            for fi in self.featureItems:
                print 'Compute %s' % fi.__str__()
                F = fi.compute(data)

class FeatureBase():
    def __init__(self):
        self.featureFunktor = None
    
    def compute(self, dataItem):
        return None
    
class LocalFeature(FeatureBase):
    def __init__(self, name, maskSize, featureFunktor):
        self.maskSize = maskSize
        self.sigma = maskSize / 3
        self.featureFunktor = featureFunktor
    
    def compute(self, dataItem):
        return self.featureFunktor()(dataItem.data, self.sigma)
    
    def __str__(self):
        return '%s: Masksize=%d, Sigma=%5.3f' % (self.featureFunktor.__name__ , self.maskSize, self.sigma)


def gaussianGradientMagnitude():
    return vm.gaussianGradientMagnitude

def structureTensor():
    return vm.structureTensor

def hessianMatrixOfGaussian():
    return vm.hessianMatrixOfGaussian

def identity():
    return lambda x, sigma: x


ilastikFeatures = []
ilastikFeatures.append(LocalFeature("Identity", 0, identity))
ilastikFeatures.append(LocalFeature("GradientMag", 3, gaussianGradientMagnitude))
ilastikFeatures.append(LocalFeature("GradientMag", 7, gaussianGradientMagnitude))
ilastikFeatures.append(LocalFeature("structureTensor", 3, structureTensor))
ilastikFeatures.append(LocalFeature("structureTensor", 7, structureTensor))
ilastikFeatures.append(LocalFeature("hessianMatrixOfGaussian", 3, hessianMatrixOfGaussian))
ilastikFeatures.append(LocalFeature("hessianMatrixOfGaussian", 7, hessianMatrixOfGaussian))