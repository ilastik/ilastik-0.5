import Image,ImageDraw, ImageFont, os
import numpy
from random import randint
class exporterToIm(object):
    
    def __init__(self,folder,Gyrus,Dapy_channel,Cells,BrdU_channel,Dcx,Dcx_channel):
        
        self.dirresultsimages=folder
        if not os.path.exists(self.dirresultsimages): os.mkdir(self.dirresultsimages)
        
        self.Gyrus=Gyrus
        self.Cells=Cells
        self.Dcx=Dcx
        self.BrdUChannel=BrdU_channel.view(numpy.ndarray).astype(numpy.uint8)
        self.DapyChannel=Dapy_channel
        self.DcxChannel=Dcx_channel
        
        self.coloredVolume=None
        
    def export(self):
        
        self._exportImages()
    
    
    def _exportImages(self):
        
        self._colorTheCells()
                
        for i in range(self.Gyrus.segmented.shape[-1]):
            dapyIm=self.BrdUChannel[:,:,i].T
            segmentedGyrIm=self.Gyrus.segmented[:,:,i].T.astype(numpy.uint8)*255
            
            im1=Image.fromarray(segmentedGyrIm)
            im1=im1.convert("RGB")
            im2=self.getImFromColeredVolume(i)
            
            im=Image.blend(im1, im2,0.9)
            
            for k in self.Cells.DictCenters.iterkeys():
                x=self.Cells.DictCenters[k][0]
                y=self.Cells.DictCenters[k][1]
                z=self.Cells.DictCenters[k][2]
                if z==i:
                    self._drawText(im,(x,y),str(k))
            
            im.save(self.dirresultsimages + '/res_' +str(i) +'.tiff', "TIFF" )
    
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
    
    def getImFromColeredVolume(self,i):
        slice=self.coloredVolume[:,:,i,:]
        slice=numpy.swapaxes(slice, 0, 1)
        #print "here", slice.shape
        im=Image.fromarray(slice,"RGB")
       
        return im
    
    def _randColor(self):
        return [randint(0, 150), randint(0, 255), randint(0, 200)]

     
        
    def _drawText(self,im,pos=(0,0),str="0",size=int(12)):
        font_path="/usr/share/fonts/truetype/freefont/FreeSerif.ttf"
        font=ImageFont.truetype(font_path,12)     
        
        draw = ImageDraw.Draw(im)
        
        draw.text(pos,str,font=font, fill="red")
    
    def _combineArray(self,arr1,arr2,alfa=0.9):
        return (alfa*(arr1)+(1-alfa)*arr2).astype(numpy.uint8)
    def _combineImage(self,image1,image2,alfa=0.9):
        temp=(alfa*(image1)+(1-alfa)*image2)
        #print type(temp), temp.dtype, temp.shape, temp.max(), temp.min()
        
        im=Image.fromarray(temp.astype(numpy.uint8))
        return im.convert("RGB")
    
    def _makeRGB(self,image):
        list=[image,image,image]
        return numpy.concatenate(list,axis=-1)
    
    def _extractRandomColor(self):
        return [255,0,0]
    
    
    def _pickleStuff(self,obj,name):
        """for debug purpose"""
        import pickle
        print "pickling " + name
        output = open(name+'.pkl', 'wb')
        pickle.dump(obj,output)
        output.close()


##################################################################TESTING#######################


def load(filename):
    import pickle
    file_pkl=open(filename,'rb')
    obj=pickle.load(file_pkl)
    file_pkl.close()
    return obj





        
if __name__=="__main__":
    testdataFolder='/home/lfiaschi/Desktop/ilastik-0.5.06-cells-counting-ready/ilastik/modules/cells_module/core/test_exporter/'
    testResultsFolder='/home/lfiaschi/Desktop/ilastik-0.5.06-cells-counting-ready/ilastik/modules/cells_module/core/test_exporter/Results'
    if not os.path.exists(testResultsFolder): os.mkdir(testResultsFolder)

    BrdU_channel=load(testdataFolder+'BrdU_ch.pkl')
    Cells=load(testdataFolder+'Cells.pkl')
    
    Dcx_channel=load(testdataFolder+'Dcx_ch.pkl')
    Dcx=load(testdataFolder+'Dcx.pkl')
    
    Dapy_channel=load((testdataFolder+'Dapy_ch.pkl'))
    Gyrus=load(testdataFolder+'Gyrus.pkl')
    
    print "creating the ex"
    ex=exporterToIm(testResultsFolder,Gyrus,Dapy_channel,Cells,BrdU_channel,Dcx,Dcx_channel)
    print "export"
    ex.export()
    print "END"
