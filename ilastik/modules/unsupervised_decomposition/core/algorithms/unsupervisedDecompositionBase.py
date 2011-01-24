class UnsupervisedDecompositionBase(object):
    #human readable information
    name = "Base Unsupervised Decomposition"
    description = "virtual base class"
    author = "HCI, University of Heidelberg"
    homepage = "http://hci.iwr.uni-heidelberg.de"

    #minimum required isotropic context
    #0 means pixel based classification
    #-1 means whole dataset - segmentation plugins normally need the whole volume for segmentation
    minContext = -1

    def __init__(self):
        pass

    def decompose(self, features):
        pass
    
    def configure(self, options):
        pass
