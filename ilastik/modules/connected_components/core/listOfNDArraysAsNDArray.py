import numpy

class ListOfNDArraysAsNDArray:

    """     

    Helper class that behaves like an ndarray, but consists of an array of ndarrays

    """     

    def __init__(self, ndarrays):     

        self.ndarrays = ndarrays
        self.dtype = ndarrays[0].dtype
        self.shape = (len(ndarrays),) + ndarrays[0].shape
        for idx, it in enumerate(ndarrays):
            if it.dtype != self.dtype or self.shape[1:] != it.shape:
                print "########### ERROR ListOfNDArraysAsNDArray all array items should have same dtype and shape (array: ", self.dtype, self.shape, " item : ",it.dtype, it.shape , ")"
        #Yes, this is horrible. But otherwise we have to copy.
        if len(self.ndarrays)==1:
            self.flat = self.ndarrays[0].flat


    def __getitem__(self, key):     
        return self.ndarrays[key[0]][tuple(key[1:])]  

    def __setitem__(self, key, data):
        self.ndarrays[key[0]][tuple(key[1:])] = data
        print "##########ERROR ######### : ListOfNDArraysAsNDArray not implemented"
    
    def flatten(self):
        if len(self.ndarrays)==1:
            return self.ndarrays[0].flatten()
        else:
            print "##########ERROR ######### : ListOfNDArraysAsNDArray not implemented"