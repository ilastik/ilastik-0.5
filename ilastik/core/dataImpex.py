
import numpy
import vigra
import os
import warnings
import pickle
import struct
import array

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import h5py

from ilastik.core import dataMgr
from ilastik.core.volume import DataAccessor as DataAccessor
from ilastik.core.overlayMgr import OverlayItem
from ilastik.core.overlayAttributes import OverlayAttributes
from ilastik.core.LOCIwrapper import reader as LOCIreader

#*******************************************************************************
# D a t a I m p e x                                                            *
#*******************************************************************************

class DataImpex(object):
    """
    Data Import/Export class 
    """
        
    @staticmethod
    def loadVolumeFromGroup(h5grp):
        di = DataItemImage
    
    @staticmethod
    def importDataItem(filename, options):
        #call this method when you expect to get a single _data item back, such
        #as when you load a stack from a directory
        if isinstance(filename, list):
            image = DataImpex.loadStack(filename, options, None)
            if image is not None:
                #the name will be set in the calling function
                theDataItem = DataImpex.initDataItemFromArray(image, "Unknown Name")
                return theDataItem
        else:
            #this is just added for backward compatibility with 'Add' button
            #of the Project Dialog
            return DataImpex.loadFromFile(filename)
    
    @staticmethod
    def importDataItems(fileList, options):
        #call this method when you expect len(fileList[0]) items back, such as
        #when you load images (even only one image) from files.
        itemList = []
        if len(fileList)==0:
            return itemList
        fileName = fileList[options.channels[0]][0]
        fBase, fExt = os.path.splitext(fileName)
        formatList = vigra.impex.listExtensions().split(' ')
        formatList.append("h5")
        if fExt == '.h5':
            theDataItem = dataMgr.DataItemImage(fileName)
            f = h5py.File(fileName, 'r')
            g = f['volume']
            theDataItem.deserialize(g, options.offsets, options.shape)
            itemList.append(theDataItem)       
        elif str(fExt)[1:] in formatList:
            image = DataImpex.loadStack(fileList, options, None)
            if image is not None:
                for item in range(image.shape[3]):
                    theDataItem = DataImpex.initDataItemFromArray(image[:, :, :, item, :], fileList[options.channels[0]][item])
                    itemList.append(theDataItem)
        elif fExt == '.img':
            #reading an Analyze 7.5 file
            image = DataImpex.readHdrImgFiles(fBase)
            theDataItem = DataImpex.initDataItemFromArray(image, fileName)
            itemList.append(theDataItem)
        
        else:
            for file in fileList:
                seriesList=LOCIreader(file[0])
                i=1
                for series in seriesList:
         
                    theDataItem = DataImpex.initDataItemFromArray(series,"series"+str(i))
                    i+=1
                    itemList.append(theDataItem)
                    
        return itemList
        
    @staticmethod
    def loadFromFile(fileName):
        # Load an image or a stack from a single file
        theDataItem = dataMgr.DataItemImage(fileName)
        print fileName
        fBase, fExt = os.path.splitext(fileName)
        if fExt == '.h5':
            f = h5py.File(fileName, 'r')
            g = f['volume']
            theDataItem.deserialize(g)

        else:
            # I have to do a cast to at.Image which is useless in here, BUT, when i py2exe it,
            # the result of vigra.impex.readImage is numpy.ndarray? I don't know why... (see featureMgr compute)
            
            data = DataImpex.vigraReadImageWrapper(fileName)

            dataAcc = DataAccessor(data)
            theDataItem._dataVol = dataAcc
        theDataItem.updateOverlays()
        return theDataItem
    
    @staticmethod
    def vigraReadImageWrapper(fileName):
        data = vigra.impex.readImage(fileName).swapaxes(0,1).view(numpy.ndarray)
        fBase, fExt = os.path.splitext(fileName)
        
        # Check for bug in Olympus microscopes
        if data.max() > 2**15 and fExt in ['.tif','.tiff']:
            print "Detected Olympus microscope bug..."
            data = (data - 2**15).astype(numpy.uint16)
 
        #remove alpha channel
        if len(data.shape) == 3:
            # prevent transparent channel
            if data.shape[2] == 4:
                data = data[:,:,0:-1]
            # vigra axistag version now delivers always a '1'
            # for the channel dimension, to support
            # both vigra versions we delete the singleton
            elif data.shape[2] == 1:
                data = data[:,:,0]
        
        return data
        
        

    @staticmethod
    def loadStack(fileList, options, logger = None):
        #This method also exports the stack as .h5 file, if options.destfile is not None
        if (len(fileList) == 0):
            return None
        if len(fileList)>1:
            nch = len(fileList)
        else:
            nch = options.rgb
        try: 
            image = numpy.zeros(options.shape+(nch,), 'float32')
        except Exception, e:
            #QtGui.QErrorMessage.qtHandler().showMessage("Not enough memory, please select a smaller Subvolume. Much smaller !! since you may also want to calculate some features...")
            #TODO: test if it really throws correctly
            print "Out of memory:", e
            raise MemoryError
        
        #loop over provided images
        z = 0
        allok = True
        for ich in range(nch):
            z = 0
            for index, filename in enumerate(fileList[ich]):
                if z >= options.offsets[2] and z < options.offsets[2] + options.shape[2]:
                    try:
                        img_data = DataImpex.vigraReadImageWrapper(filename)
                        #Why did we need this options.rbg thing? Why not always load all channels?
                        if options.rgb>1:
                            image[:,:,z-options.offsets[2],:] = img_data[options.offsets[0]:options.offsets[0]+options.shape[0], options.offsets[1]:options.offsets[1]+options.shape[1],:]
                        else:
                            image[:, :, z-options.offsets[2], ich] = img_data[options.offsets[0]:options.offsets[0]+options.shape[0], options.offsets[1]:options.offsets[1]+options.shape[1]]
                        if logger is not None:                           
                            logger.insertPlainText(".")
                    except Exception, e:
                        allok = False
                        print e 
                        s = "Error loading file " + filename + "as Slice " + str(z-options.offsets[2])
                        if logger is not None:
                            logger.appendPlainText(s)
                            logger.appendPlainText("")
                    if logger is not None:        
                        logger.repaint()
                z = z + 1

        if options.invert:
            image = 255 - image             
                 
        if options.destShape is not None:
            result = numpy.zeros(options.destShape + (nch,), 'float32')
            for i in range(nch):
                cresult = vigra.filters.gaussianSmoothing(image[:,:,:,i].view(vigra.Volume), 2.0)
                cresult = vigra.sampling.resizeVolumeSplineInterpolation(cresult,options.destShape)
                result[:,:,:,i] = cresult[:,:,:]
            image = result
        else:
            options.destShape = options.shape
        
        

        if options.grayscale:
            image = image.view(numpy.ndarray)
            result = numpy.average(image, axis = 3)
            options.rgb = 1
            image = result.astype(numpy.uint8)
            image.reshape(image.shape + (1,))
            nch = 1
            
        if options.normalize:
            maximum = numpy.max(image)
            minimum = numpy.min(image)
            image = (image - minimum) * (255.0 / (maximum - minimum)) 
            image = image.astype(numpy.uint8)
        
        image = image.reshape(1,options.destShape[0],options.destShape[1],options.destShape[2],nch)
        print options.destfile
        try:
            if options.destfile != None:
                print "Saving to file ", options.destfile
                f = h5py.File(options.destfile, 'w')
                g = f.create_group("volume") 
                temp_image = image.swapaxes(3,1) 
                temp_image = temp_image.swapaxes(2,3)      
                g.create_dataset("data",data=temp_image)
                f.close()
        except:
            print "ERROR saving File ", options.destfile
            
        if allok:
            return image

    @staticmethod
    def initDataItemFromArray(image, name):
        dataItem = dataMgr.DataItemImage(name)
        dataItem._dataVol = DataAccessor(image, True)
        dataItem.updateOverlays()
        return dataItem

    @staticmethod
    def readShape(filename):
        #read the shape of the dataset
        #return as (x, y, z, c)
        fBase, fExt = os.path.splitext(filename)
        if fExt == '.h5':
            f = h5py.File(filename, 'r')
            shape = f["volume/data"].shape
            if shape[1] == 1:
                #2d _data looks like (1, 1, x, y, c)
                return (shape[2], shape[3], 1, shape[4])
            else:
                #3d data looks like (1, x, y, z, c)
                return (shape[1], shape[2], shape[3], shape[4])
        
        elif fExt == '.img':
            #analyze 7.5 file, read the shape from corresponding hdr file
            stuff = DataImpex.readHdrImgShape(fBase)
            print "...reading analyze 7.5 image with ", stuff[0][0], "channels..."
            return (int(stuff[0][3]),int(stuff[0][2]),int(stuff[0][1]),int(stuff[0][0]))
        
        else :
            try:
                tempimage = DataImpex.vigraReadImageWrapper(filename)
            except Exception, e:
                print e
                raise
            if (len(tempimage.shape)==3):
                return (tempimage.shape[0], tempimage.shape[1], 1, tempimage.shape[2])
            else:
                return (tempimage.shape[0], tempimage.shape[1], 1, 1)

    @staticmethod                
    def importOverlay(dataItem, filename, prefix="File Overlays/", attrs=None):
        theDataItem = DataImpex.importDataItem(filename, None)
        if theDataItem is None:
            print "could not load", filename
            return None

        data = theDataItem[:,:,:,:,:]

        if attrs == None:
            attrs = OverlayAttributes(filename)
        if attrs.min is None:
            attrs.min = numpy.min(data)
        if attrs.max is None:
            attrs.max = numpy.max(data)
            
        if data.shape[0:-1] == dataItem.shape[0:-1]:
            ov = OverlayItem(data, color = attrs.color, 
                             alpha = attrs.alpha, 
                             colorTable = attrs.colorTable,
                             autoAdd = attrs.autoAdd,
                             autoVisible = attrs.autoVisible,
                             min = attrs.min, max = attrs.max)
            ov.key = attrs.key
            if len(prefix) > 0:
                if prefix[-1] != "/":
                    prefix = prefix + "/"
            dataItem.overlayMgr[prefix + ov.key] = ov            
            return ov
       
    @staticmethod
    def exportOverlay(filename, format, overlayItem, timeOffset = 0, sliceOffset = 0, channelOffset = 0):
        if format == "h5":
            filename = filename + "." + format
            f = h5py.File(filename, 'w')
            path = overlayItem.key
            #pathparts = path.split("/")
            #pathparts.pop()
            #prevgr = f.create_group(pathparts.pop(0))
            #for item in pathparts:
            prevgr = f.create_group("volume")
            #try:
            data = numpy.ndarray(overlayItem._data.shape, overlayItem._data.dtype)
            data[0,:,:,:,:] = overlayItem._data[0,:,:,:,:]
            dataset = prevgr.create_dataset("data", compression = "gzip", data=data)
            dataset.attrs["overlayKey"] = str(overlayItem.key)
            dataset.attrs["overlayColor"] = pickle.dumps(overlayItem.color)
            dataset.attrs["overlayColortable"] = pickle.dumps(overlayItem.colorTable)
            dataset.attrs["overlayMin"] = pickle.dumps(overlayItem.min)
            dataset.attrs["overlayMax"] = pickle.dumps(overlayItem.max)
            dataset.attrs["overlayAutoadd"] = pickle.dumps(overlayItem.autoAdd)
            dataset.attrs["overlayAutovisible"] = pickle.dumps(overlayItem.autoVisible)
            dataset.attrs["overlayAlpha"] = pickle.dumps(overlayItem.alpha)
            #overlayItemReference.name, data=overlayItemReference.overlayItem._data[0,:,:,:,:])
            #except Exception, e:
            #    print e
            f.close()
            return
        
        if overlayItem._data.shape[1]>1:
            #3d _data
            for t in range(overlayItem._data.shape[0]):
                for z in range(overlayItem._data.shape[3]):
                    for c in range(overlayItem._data.shape[-1]):
                        fn = filename
                        data = overlayItem._data[t,:,:,z,c]
                        if overlayItem._data.shape[0]>1:
                            fn = fn + ("_time%03i" %(t+timeOffset))
                        fn = fn + ("_z%05i" %(z+sliceOffset))
                        if overlayItem._data.shape[-1]>1:
                            fn = fn + ("_channel%03i" %(c+channelOffset))
                        fn = fn + "." + format
                        
                        dtype_ = None
                        if data.dtype == numpy.float32:
                            mi = data.min()
                            ma = data.max()
                            if mi >= 0 and 1 < ma <= 255:
                                data = data.astype(numpy.uint8)
                                dtype_ = 'NATIVE'
                            else:
                                dtype_ = numpy.uint8
                        
                        vigra.impex.writeImage(data.swapaxes(1,0), fn, dtype=dtype_)
                        print "Exported file ", fn
        else:
            for t in range(overlayItem._data.shape[0]):
                for c in range(overlayItem._data.shape[-1]):
                    fn = filename
                    data = overlayItem._data[t, 0, :, :, c]
                    if overlayItem._data.shape[0]>1:
                        fn = fn + ("_time%03i" %(t+timeOffset))
                    if overlayItem._data.shape[-1]>1:
                        fn = fn + ("_channel%03i" %(c+channelOffset))
                    fn = fn + "." + format
                    
                    # dtype option for tif images when dtype is not uint8
                    # specifing dtype in the write function leads to scaling!
                    # be careful nbyte also scales, which is typically fine
                    if data.dtype == numpy.float32:
                        mi = data.min()
                        ma = data.max()
                        if mi >= 0 and 1 < ma <= 255:
                            data = data.astype(numpy.uint8)
                            dtype_ = 'NATIVE'
                        else:
                            dtype_ = numpy.uint8
                    
                    vigra.impex.writeImage(data, fn, dtype=dtype_)
                    print "Exported file ", fn

    @staticmethod
    def exportFormatList():
        formats = vigra.impex.listExtensions().split(' ')
        formats = [x for x in formats if x in ['png', 'tif']]
        return formats


    @staticmethod
    def readHdrImgShape(filename):
        #filename should be passed without an extension
        hdr_filename = filename+'.hdr'
        number_of_elements_short = 38
        number_of_elements_float = 8
        bytes_for_short = 2
        bytes_for_float = 4
        point_with_dim_begins = 20
        short_values = numpy.zeros(shape=(number_of_elements_short,1))
        float_values = numpy.zeros(shape=(number_of_elements_float,1))
        with open(hdr_filename, 'rb') as f1:
            for i in range(len(short_values)):
                short_values[i] = struct.unpack('h', f1.read(bytes_for_short))[0]
            for j in range(len(float_values)):
                float_values[j] = struct.unpack('f', f1.read(bytes_for_float))[0]
        
        number_of_dim = sum(short_values[point_with_dim_begins])
        
        # we create an array 'dim' with values of dimensions of image file
        dim = list()
        for k in range(1, int(number_of_dim+1)):
            dim.append(int(sum(short_values[point_with_dim_begins+k])))
         
        #print dim[0], dim[1], dim[2], dim[3]
        bitpix = sum(short_values[36])
        return dim, bitpix, short_values

    @staticmethod
    def readHdrImgFiles(filename):
        #filename should be passed without extension
        #Read header file to identify the dimensions of image in .img file, 
        #pixel depth and pixel dimension, because this information we need to 
        #arrange information from .img file in numpy.ndarray correctly.
        #We read all first 38 elements from file with decoding in int_short format. 
        #And next 8 elements with decoding in float format. 
        #All information concerning the location of relevant data in .hdr and .img 
        #you can find by taking look at format description: http://eeg.sourceforge.net/ANALYZE75.pdf
        #Written by Darya Trofimova

        dim, bitpix, short_values = DataImpex.readHdrImgShape(filename)
        # need to make a operator for doing this
        #FIXME: why do we need this variable? it's not used anywhere. 
        #FIXME: comment out for now
        '''
        pix_dim = list()
        pix_dim = map(float, pix_dim)
        for l in range(1,4):
            pix_dim.append(sum(float_values[l]))
        '''
        #we need here to indicate 'bytes' and 'decode' somehow. 
        #We do it knowing the size of bitpix from .hdr file.
        
        result1 = {
          '16': lambda: 'h',
          '32': lambda: 'i',
          '64': lambda: 'f'
          }
        decode = result1.get(str(int(bitpix)))()
          
        result2 = {
          '16': lambda: '2',
          '32': lambda: '4',
          '64': lambda: '8'
          }
        bytes = int(result2.get(str(int(bitpix)))())
          
        #Read the .img file with the decoding format, bytes and size information from the header file.
          
        img_filename = filename+'.img'
        totalBytes = os.path.getsize(img_filename)
        number_var = totalBytes/bytes
        #print number_var
        img_values = numpy.zeros(shape=(1,int(dim[3]),int(dim[2]),int(dim[1]),int(dim[0])), dtype=numpy.int16)
        #print img_values.shape
        with open(img_filename, 'rb') as f2:
            for i in reversed(range(int(dim[2]))):
                for j in range(int(dim[1])):
                    for k in range(int(dim[0])):
                        img_values[0,0,i,j,k] = struct.unpack(decode, f2.read(bytes))[0]
        
        #the counter i must go in opposite direction because we want our picture's (0, 0) 
        #in the left top corner.
        #img_values = img_values.reshape((dim[0],dim[1],dim[2]))
        
        return img_values 
            
