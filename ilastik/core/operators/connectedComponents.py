from ilastik.core.graph.nonArrayData import  VersionedDict
from ilastik.core.graph.blockArray import BlockArray
from ilastik.core.operators.operatorBase import OperatorBase

import vigra, numpy

#*******************************************************************************
# T h r e s h o l d i n g                                       *
#*******************************************************************************

class ConnectedComponents(OperatorBase):
    #***************************************************************************
    # P a r a m e t e r                                                        *
    #***************************************************************************
    class Parameter(OperatorBase):
        def __init__(self, workflow):
            OperatorBase.__init__(self, workflow, "thresholding_parameter_operator", [], ['out'])
            self.neighborhood = 6
            self.backgroundLabel = 0
        def setBackgroundLabel(self, backgroundLabel):
            self.backgroundLabel = backgroundLabel
        def setNeighborhood(self, neighborhood):
            self.neighborhood = neighborhood
        def createOutputFromInputs(self, outputName):
            self.connectOutput(outputName, VersionedDict('connectedComponents_parameter', {'neighborhood': self.neighborhood, 'backgroundLabel': self.backgroundLabel}))
        def output(self):
            return self.getOutputData('out')
        def backprojectROI(self, roi=None):
            return None
        def execute(self, inputs, outputs):
            outputs['out'].data = {'neighborhood': self.neighborhood, 'backgroundLabel': self.backgroundLabel}
    
    def __init__(self, workflow, blockshape=None):
        OperatorBase.__init__(self, workflow, 'connectedComponents', ['in', 'parameter'], ['out'])
        self.blockshape = blockshape
        
        self.dilation = None
    
    def setParameter(self, connectedComponentsParameter):
        self.connectInput('parameter', connectedComponentsParameter)
    
    def setInput(self, input):
        self.connectInput('in', input)
    
    def output(self):
        return self.getOutputData('out')
    
    def createOutputFromInputs(self, outputName):
        outputShape = self.inputSlots['in'].data.shape
        
        data = BlockArray('ConnectedComponents', outputShape, self.blockshape, dtype=numpy.uint32)
        self.connectOutput(outputName, data)

    def execute(self, inputs, outputs):
        n = inputs['parameter'].data['neighborhood']
        b = inputs['parameter'].data['backgroundLabel']
        if inputs['in'].data.ndim == 3:
            outData = vigra.analysis.labelVolumeWithBackground(numpy.require(inputs['in'].data,dtype=numpy.float32), n, b)
        elif inputs['in'].data.ndim == 2:
            outData = vigra.analysis.labelImageWithBackground(numpy.require(inputs['in'].data,dtype=numpy.float32), 4, b)
            
        
        outputs['out'].data = outData
        
    def backprojectROI(self, roi=None):
        return None
