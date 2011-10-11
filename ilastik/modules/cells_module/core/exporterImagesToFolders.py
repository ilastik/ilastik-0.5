
import numpy
from random import randint
import os
import vigra
import h5py

from numpy import require,uint8,float32

import qimage2ndarray

from PyQt4.QtGui import *
from PyQt4.QtCore import *


def blend(im1,im2,alpha):
    
    assert im1.shape[-1]==3,"%f"%im1.shape[-1]
    assert im1.shape==im2.shape
    res=numpy.where(im2!=0,im1*(1-alpha)+alpha*im2.astype(numpy.float32),im1)
    return res.astype(uint8)

def Gray2RGB(im):
    temp=numpy.zeros(im.shape+(1,),dtype=numpy.uint8)
    temp[...,0]=im
    return numpy.concatenate([temp,temp,temp],axis=-1).astype(uint8)

def RGB2Gray(im):
    return numpy.mean(im,axis=-1).astype(uint8)
    
def colorMask(mask,color=[255,0,0]):
    res=Gray2RGB(mask)
    
    res[...,0]=numpy.where(mask!=0,color[0],0)
    res[...,1]=numpy.where(mask!=0,color[1],0)
    res[...,2]=numpy.where(mask!=0,color[2],0)
    return res

    
def draw(im,Labels):
    labels=Labels.astype(numpy.uint32)
    #print labels.shape
    c1=vigra.analysis.regionImageToEdgeImage(labels,1)
    im2=im.copy()
    if im2.shape[-1]==1: im2=numpy.dstack([im2,im2,im2])
    im2[:,:,0]=numpy.where(c1!=0,0,im2[:,:,0])
    im2[:,:,1]=numpy.where(c1!=0,255,im2[:,:,1])
    im2[:,:,2]=numpy.where(c1!=0,0,im2[:,:,2])
    return im2
    
class exporterToIm(object):
    
    def __init__(self,folder,Gyrus,Dapy_channel,Cells,BrdU_channel,Dcx,Dcx_channel):
        self.app=QApplication([])
        
        self.dirresultsimages=folder
        if not os.path.exists(self.dirresultsimages): os.mkdir(self.dirresultsimages)
        
        self.Gyrus=Gyrus
        self.Cells=Cells
        self.Dcx=Dcx
        self.BrdUChannel=BrdU_channel.view(numpy.ndarray).astype(numpy.uint8)
        self.DapyChannel=Dapy_channel.view(numpy.ndarray).astype(numpy.uint8)
        self.DcxChannel=Dcx_channel.view(numpy.ndarray).astype(numpy.uint8)
        
        self.coloredVolume=None
        
    def export(self):
        self._colorTheCells()
        self._exportToHdf5()
        self._exportGyrusImages()
        self._exportImagesCells()
        self._exportImagesDcx()
    
    def _exportToHdf5(self):
        h,t=name=os.path.split(self.dirresultsimages)
        name=os.path.join(self.dirresultsimages,t+'_processed.h5')
        #print name
        f=h5py.File(name,'w')
        g=f.create_group('ch0')
        g.create_dataset('ch0_raw',shape=self.DapyChannel.shape,data=self.DapyChannel)
        g.create_dataset('ch0_interior',shape=self.Gyrus.interior.shape,data=self.Gyrus.interior)
        g.create_dataset('ch0_segmented',shape=self.Gyrus.segmented.shape,data=self.Gyrus.segmented)
        g.create_dataset('ch0_Pmap',shape=self.Gyrus.probMap.shape,data=self.Gyrus.probMap)
        
        
        g=f.create_group('ch1')
        g.create_dataset('ch1_raw',shape=self.BrdUChannel.shape,data=self.BrdUChannel)
        g.create_dataset('ch1_segmented_cells',shape=self.Cells.segmented.shape,dtype=self.Cells.segmented.dtype,data=self.Cells.segmented)
        g.create_dataset('ch1_Pmap',shape=self.Cells.probMap.shape,data=self.Cells.probMap)
        self._serializeDictToHdf5(g, 'positions', self.Cells.DictPositions)
        self._serializeDictToHdf5(g, 'centers', self.Cells.DictCenters)
        
        
        
        g=f.create_group('ch2')
        g.create_dataset('ch2_raw',shape=self.DcxChannel.shape,data=self.DcxChannel)
        g.create_dataset('ch2_Pmap',shape=self.Dcx.probMap.shape,data=self.Dcx.probMap)
        self._serializeDictToHdf5(g, 'intensities', self.Dcx.DictIntDcX)
        f.close()
        
    
    def _serializeDictToHdf5(self,g,name,diction):
        g2=g.create_group(name)
        for k in diction.iterkeys():
            data=numpy.array(diction[k]).T
            g2.create_dataset(str(k),shape=data.shape,dtype=data.dtype,data=data)
            
        
    
    def _exportGyrusImages(self,alpha=0.2):
        im1=Gray2RGB(self.DapyChannel)
        im2=colorMask(self.Gyrus.segmented*255,[255,0,0])
        #import pylab
        #pylab.imshow(im2[:,:,0,:])
        #pylab.show()
        im1=blend(im1,im2,alpha)
        im2=colorMask(self.Gyrus.interior*255,[0,255,0])
        im1=blend(im1,im2,alpha)
        for z in range(im1.shape[-2]):
            name=os.path.join(self.dirresultsimages,"gyrus%.2d.png"%z)
            #print name
            vigra.impex.writeImage(im1[:,:,z,:],name)
    
    def _exportImagesCells(self):
                        
        for i in range(self.coloredVolume.shape[-2]):
            im=self.coloredVolume[:,:,i,:]
            
            name=os.path.join(self.dirresultsimages,"cells%.2d.png"%i)
            shape=im.shape
            im=qimage2ndarray.array2qimage(im)#.swapaxes(0,1))
            
            
     
            
            for k in self.Cells.DictCenters.iterkeys():
                x=self.Cells.DictCenters[k][0]
                y=self.Cells.DictCenters[k][1]
                z=self.Cells.DictCenters[k][2]
                if z==i:
                   
                    self._drawText(im,(x,y),str(k))
            
            im=qimage2ndarray.rgb_view(im)#.swapaxes(0,1)        
            vigra.impex.writeImage(draw(im,self.Gyrus.segmented[:,:,i]+self.Gyrus.interior[:,:,i]),name)
         
    def _exportImagesDcx(self):
                        
        for i in range(self.DcxChannel.shape[-1]):
            im=Gray2RGB(self.DcxChannel[:,:,i])
            
            name=os.path.join(self.dirresultsimages,"dcx%.2d.png"%i)
            shape=im.shape
            im=qimage2ndarray.array2qimage(im)#.swapaxes(0,1))
            
            
     
            
            for k in self.Cells.DictCenters.iterkeys():
                x=self.Cells.DictCenters[k][0]
                y=self.Cells.DictCenters[k][1]
                z=self.Cells.DictCenters[k][2]
                if z==i:
                   
                    self._drawText(im,(x,y),str(k))
            
            im=qimage2ndarray.rgb_view(im)#.swapaxes(0,1)        
            vigra.impex.writeImage(draw(im,self.Gyrus.segmented[:,:,i]+self.Gyrus.interior[:,:,i]),name)    
    def _colorTheCells(self):
        xh=self.BrdUChannel.shape[0]
        yh=self.BrdUChannel.shape[1]
        zh=self.BrdUChannel.shape[2]
        
        temp=self.BrdUChannel.copy()
        #print temp.shape
        temp.shape=temp.shape+(1,)
        temp=numpy.concatenate([temp,temp,temp],axis=-1)
        #print temp.shape
        for k in self.Cells.DictPositions.iterkeys():
            x=self.Cells.DictPositions[k][0]
            y=self.Cells.DictPositions[k][1]
            z=self.Cells.DictPositions[k][2]
                    
            temp[x,y,z,:]=self._randColor()
        
        self.coloredVolume=temp

    def _randColor(self):
        return [randint(0, 150), randint(0, 255), randint(0, 200)]

    
    def _pickleStuff(self,obj,name):
        """for debug purpose"""
        import pickle
        print "pickling " + name
        output = open(name+'.pkl', 'wb')
        pickle.dump(obj,output)
        output.close()
        
    def _drawText(self,im,pos,string):
        p=QPainter(im)
        p.setPen(QColor(255,0,0))
        y,x=pos
        
        p.drawText(QRectF(x,y,200,200),QString(str(string)))
        #p.drawText(QRect(0, 0, 100, 100));
        
        p.end()
        #im.save('test.png')
        #im=qimage2ndarray.rgb_view(im)
        return im


##################################################################TESTING#######################


def load(filename):
    import pickle
    file_pkl=open(filename,'rb')
    obj=pickle.load(file_pkl)
    file_pkl.close()
    return obj





        
if __name__=="__main__":
    testdataFolder='/Users/lfiaschi/phd/workspace/ilastik-github/ilastik/modules/cells_module/core/test_data_batch/test-exported-images/'
    testResultsFolder='/Users/lfiaschi/phd/workspace/ilastik-github/ilastik/modules/cells_module/core/test_data_batch/test-exported-images/results'
    if not os.path.exists(testResultsFolder): os.mkdir(testResultsFolder)

    BrdU_channel=load(testdataFolder+'BrdU_ch.pkl')
    Cells=load(testdataFolder+'Cells.pkl')
    
    a={1: [range(100,150),range(100,150),list(numpy.zeros(50))]}
    Cells.DictPositions=a
    Cells.DictCenters={1: [120,120,0]}
    Cells.DictCenters={2: [202,220,0],1:[120,120,0]}
    Dcx_channel=load(testdataFolder+'Dcx_ch.pkl')
    Dcx=load(testdataFolder+'Dcx.pkl')
    
    Dapy_channel=load((testdataFolder+'Dapy_ch.pkl'))
    Gyrus=load(testdataFolder+'Gyrus.pkl')
    
    #print "creating the ex"
    ex=exporterToIm(testResultsFolder,Gyrus,Dapy_channel,Cells,BrdU_channel,Dcx,Dcx_channel)
    print "export ... . . . . .. . . . . . .. . . . .. . . . .. . . . .. . . . . . .. . . .. . "
    ex.export()
    print "END"
