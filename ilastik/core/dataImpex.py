
import numpy
import vigra
import os
import h5py

from ilastik.core import dataMgr
from ilastik.core.volume import DataAccessor as DataAccessor
from ilastik.core.volume import Volume as Volume

class DataImpex(object):
    """
    Data Import/Export class 
    """
        
    @staticmethod
    def loadVolumeFromGroup(h5grp):
        di = DataItemImage
    
    @staticmethod
    def importDataItem(filename, options):
        #call this method when you expect to get a single data item back, such
        #as when you load a stack from a directory
        if isinstance(filename, list):
            image = DataImpex.loadStack(filename, options, None)
            if image is not None:
                #the name will be set in the calling function
                theDataItem = DataImpex.initDataItemFromArray(image, "bla")
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
        if fExt == '.h5':
            theDataItem = dataMgr.DataItemImage(fileName)
            f = h5py.File(fileName, 'r')
            g = f['volume']
            theDataItem.deserialize(g, options.offsets, options.shape)
            itemList.append(theDataItem)
        else:
            image = DataImpex.loadStack(fileList, options, None)
            if image is not None:
                for item in range(image.shape[3]):
                    theDataItem = DataImpex.initDataItemFromArray(image[:, :, :, item, :], fileList[options.channels[0]][item])
                    itemList.append(theDataItem)
        return itemList
        
    @staticmethod
    def loadFromFile(fileName):
        # Load an image or a stack from a single file
        theDataItem = dataMgr.DataItemImage(fileName)
        fBase, fExt = os.path.splitext(fileName)
        if fExt == '.h5':
            f = h5py.File(fileName, 'r')
            g = f['volume']
            theDataItem.deserialize(g)
        else:
            # I have to do a cast to at.Image which is useless in here, BUT, when i py2exe it,
            # the result of vigra.impex.readImage is numpy.ndarray? I don't know why... (see featureMgr compute)
            data = vigra.impex.readImage(fileName).swapaxes(0,1).view(numpy.ndarray)
            #data = vigra.impex.readImage(fileName).swapaxes(0,1).view(numpy.ndarray)

            dataAcc = DataAccessor(data)
            theDataItem.dataVol = Volume(dataAcc)
            print "dataVol.data", theDataItem.dataVol.data.shape
        return theDataItem

    @staticmethod
    def loadStack(fileList, options, logger = None):
        #This method also exports the stack as .h5 file, if options.destfile is not None
        if (len(fileList) == 0):
            return None
        if len(options.channels)>1:
            nch = 3
        else:
            nch = options.rgb
        try: 
            image = numpy.zeros(options.shape+(nch,), 'float32')
        except Exception, e:
            #QtGui.QErrorMessage.qtHandler().showMessage("Not enough memory, please select a smaller Subvolume. Much smaller !! since you may also want to calculate some features...")
            #TODO: test if it really throws correctly
            print e
            raise MemoryError
        
        #loop over provided images
        z = 0
        allok = True
        firstlist = fileList[options.channels[0]]
        for index, filename in enumerate(firstlist):
            if z >= options.offsets[2] and z < options.offsets[2] + options.shape[2]:
                try:
                    img_data = vigra.impex.readImage(filename).swapaxes(0,1)
                    
                    if options.rgb > 1:
                        image[:,:,z-options.offsets[2],:] = img_data[options.offsets[0]:options.offsets[0]+options.shape[0], options.offsets[1]:options.offsets[1]+options.shape[1],:]
                    else:
                        image[:,:, z-options.offsets[2],options.channels[0]] = img_data[options.offsets[0]:options.offsets[0]+options.shape[0], options.offsets[1]:options.offsets[1]+options.shape[1]]
                        #load other channels if needed
                        if (len(options.channels)>1):
                            img_data = vigra.impex.readImage(fileList[options.channels[1]][index]).swapaxes(0,1)
                            image[:,:,z-options.offsets[2],options.channels[1]] = img_data[options.offsets[0]:options.offsets[0]+options.shape[0], options.offsets[1]:options.offsets[1]+options.shape[1]]
                            if (len(options.channels)>2):                                
                                img_data = vigra.impex.readImage(fileList[options.channels[2]][index]).swapaxes(0,1)
                                image[:,:,z-options.offsets[2],options.channels[2]] = img_data[options.offsets[0]:options.offsets[0]+options.shape[0], options.offsets[1]:options.offsets[1]+options.shape[1]]
                            else:
                                #only 2 channels are selected. Fill the 3d channel with zeros
                                #TODO: zeros create an unnecessary memory overhead in features
                                #change this logic to something better
                                ch = set([0,1,2])
                                not_filled = ch.difference(options.channels)
                                nf_ind = not_filled.pop()
                                image[:,:,z-options.offsets[2],nf_ind]=0
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
                cresult = vigra.sampling.resizeVolumeSplineInterpolation(image[:,:,:,i].view(vigra.Volume),options.destShape)
                result[:,:,:,i] = cresult[:,:,:]
            image = result
        else:
            options.destShape = options.shape
        
        if options.normalize:
            maximum = numpy.max(image)
            minimum = numpy.min(image)
            image = image * (255.0 / (maximum - minimum)) - minimum

        if options.grayscale:
            image = image.view(numpy.ndarray)
            result = numpy.average(image, axis = 3)
            options.rgb = 1
            image = result.astype('uint8')
            image.reshape(image.shape + (1,))
        
        image = image.reshape(1,options.destShape[0],options.destShape[1],options.destShape[2],nch)
        
        try:
            if options.destfile != None :
                f = h5py.File(options.destfile, 'w')
                g = f.create_group("volume")        
                g.create_dataset("data",data = image)
                f.close()
        except:
            print "######ERROR saving File ", options.destfile
            
        if allok:
            return image

    @staticmethod
    def initDataItemFromArray(image, name):
        dataItem = dataMgr.DataItemImage(name)
        dataItem.dataVol = Volume(DataAccessor(image, True))
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
                #2d data looks like (1, 1, x, y, c)
                return (shape[2], shape[3], 1, shape[4])
            else:
                #3d data looks like (1, x, y, z, c)
                return (shape[1], shape[2], shape[3], shape[4])
        else :
            try:
                tempimage = vigra.impex.readImage(filename).swapaxes(0,1)
            except Exception, e:
                print e
                raise
            if (len(tempimage.shape)==3):
                return (tempimage.shape[0], tempimage.shape[1], 1, tempimage.shape[2])
            else:
                return (tempimage.shape[0], tempimage.shape[1], 1, 1)
        

     #           if self.multiChannel.checkState() > 0 and len(self.options.channels)>1:
      #      if (len(self.fileList[self.channels[0]])!=len(self.fileList[self.channels[1]])) or (len(self.channels)>2 and (len(self.fileList[0])!=len(self.fileList[1]))):
       #         QtGui.QErrorMessage.qtHandler().showMessage("Chosen channels don't have an equal number of files. Check with Preview files button")
                #should it really reject?
        #        self.reject()
        #        return        
