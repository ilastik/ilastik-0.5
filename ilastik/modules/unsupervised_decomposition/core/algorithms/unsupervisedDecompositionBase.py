#*******************************************************************************
# U n s u p e r v i s e d D e c o m p o s i t i o n B a s e                    *
#*******************************************************************************

class UnsupervisedDecompositionBase(object):
    #human readable information
    name = "Base Unsupervised Decomposition"
    description = "virtual base class"
    author = "HCI, University of Heidelberg"
    homepage = "http://hci.iwr.uni-heidelberg.de"

    def __init__(self):
        pass

    def decompose(self, features):
        pass
    
    def configure(self, options):
        pass
    
    def checkNumComponents(self, numChannels, numComponents):
        if(numChannels < numComponents):
            print "WARNING: The data set comprises", numChannels, "channels. Decomposition into more components (", numComponents, ") is not possible. Using", numChannels, "components instead."
            return numChannels
        if(numComponents < 1):
            print "WARNING: Decomposition into less than one component is not possible. Using one component instead."
            return 1
        return numComponents

    # it is probably NOT a good idea to define this a class level (more than one PLSA 
    # instance with different numbers of components might exist), but in the current 
    # ilastik architecture  this method is called before the instance is even created,  
    # so it HAS to be a class method for now
    # workaround: set self.numComponents in init function
    @classmethod   
    def setNumberOfComponents(cls, numComponents):
        cls.numComponents = numComponents
