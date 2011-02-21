#authors Luca Fiaschi, Christoph Sommer

import numpy

try:
    import jpype
except:
    print "Please install jpype if you want to read microscopy formats images like LIF."
import os


def reader(fileName=None):
    """ Function to read LIF (Leica Image Format) files. The function expects a filenames a returns a list of 5D data objects
        on item for each series contained in the LIF file. The function expects to find a running Java Virtual Machine. This Machine
        should only be started ones, so make sure it is started outside this function before you call it.
		
		This function requires jpype to be installed.
	"""
    #the switch is added to work also inside eclipse
    pathtoLOCI=os.getcwd() 
    if pathtoLOCI[-7:]!= 'ilastik':
        pathtoLOCI=os.getcwd()+ "/ilastik/core/loci_tools.jar"
    else:
        pathtoLOCI= os.getcwd() + '/core/loci_tools.jar'

    try:
        if not jpype.isJVMStarted():
            jpype.startJVM(jpype.getDefaultJVMPath(),'-Djava.class.path=' + pathtoLOCI)
    except:
        print "JVM Start failed, propably it has been started already..."	


    if fileName is None:
        print "No file name given"
        return
        
    r = jpype.JClass('loci.formats.ChannelFiller')()
    r = jpype.JClass('loci.formats.ChannelSeparator')(r)
    print fileName
    r.setId(fileName)

    seriesData = []
    numSeries = r.getSeriesCount()
    
    print "Series:", numSeries
    
    pixelType = r.getPixelType()
    bpp = jpype.JClass('loci.formats.FormatTools').getBytesPerPixel(pixelType);
    fp = jpype.JClass('loci.formats.FormatTools').isFloatingPoint(pixelType);
    sgn = jpype.JClass('loci.formats.FormatTools').isSigned(pixelType);
    bppMax=numpy.power(2,bpp*8)
    print "Data " +  str(bpp*8) + " bit detected"
    little = r.isLittleEndian();


    if sgn:
        print "ERROR: cannont interpret signed data"
        return
    

    for s in range(numSeries):
        r.setSeries(s)
        
        t = r.getSizeT()
        w = r.getSizeX()
        h = r.getSizeY()
        d = r.getSizeZ();
        c = r.getSizeC();
        
        if bpp==1:
            res = numpy.zeros((t,h,w,d,c),numpy.uint8)
        elif bpp==2:
            res = numpy.zeros((t,h,w,d,c),numpy.uint16)
        elif bpp ==4:
            res = numpy.zeros((t,h,w,d,c),numpy.uint32)
        elif bpp == 8:
            res = numpy.zeros((t,h,w,d,c),numpy.uint64)
        else:
            print "ERROR: unrecognized bit format type"
            return

        print "Time, Width, Height, Depth, Channels", t, w, h, d, c

        numImages = r.getImageCount()
        
        for i in range(numImages):

            zPos = r.getZCTCoords(i)[0]
            cPos = r.getZCTCoords(i)[1]
            tPos = r.getZCTCoords(i)[2]
            print "Images", i, "at channel", cPos , "and z-slice", zPos , "and time-point", tPos
            
            

            img = r.openBytes(i)
            arr=jpype.JClass('loci.common.DataTools').makeDataArray(img,bpp,fp,little)
            #print type(arr)

            
            data = numpy.array(arr[0:len(arr)])
            data=data.reshape((h,w))
            
            res[tPos,:,:,zPos,cPos] = data
        
        seriesData.append(res)     
    r.close()
    jpype.shutdownJVM()
    
    return seriesData
    

#*******************************************************************************
# i f   _ _ n a m e _ _   = =   " _ _ m a i n _ _ "                            *
#*******************************************************************************

if __name__ == "__main__":
    #try:
    #    if not jpype.isJVMStarted():
    #        jpype.startJVM(jpype.getDefaultJVMPath(),'-Djava.class.path=/Applications/ImageJ/plugins/loci_tools.jar')
    #except:
    #    print "JVM Start failed, propably it has been started already..."

    data = reader('ERT2Dkk1_5181_SVZ_Schnitt_1.lif')
    #arr = readLif('PU1-NBT-3dpf-e11(40stacks)-ok+.oib')
    #jpype.shutdownJVM()
    

