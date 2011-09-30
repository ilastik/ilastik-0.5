# -*- coding: utf-8 -*-
import numpy
try:
  import jpype
except:
  print "jpype is not there"

def readLif(fileName=None):
    """ Function to read LIF (Leica Image Format) files. The function expects a filenames a returns a list of 5D data objects
        on item for each series contained in the LIF file. The funciton expects to find a running Java Virtual Machine. This Machine
        should only be started ones, so make sure it is started outside this function before you call it.
		
		This function requires jpype to be installed.
	"""

    if fileName is None:
	    print "No file name given"
	    return
        
    r = jpype.JClass('loci.formats.ChannelFiller')()
    r = jpype.JClass('loci.formats.ChannelSeparator')(r)

    r.setId(fileName)

    seriesData = []
    numSeries = r.getSeriesCount()
    
    print "Series:", numSeries
    
    pixelType = r.getPixelType()
    bpp = jpype.JClass('loci.formats.FormatTools').getBytesPerPixel(pixelType);
    fp = jpype.JClass('loci.formats.FormatTools').isFloatingPoint(pixelType);
    sgn = jpype.JClass('loci.formats.FormatTools').isSigned(pixelType);

    little = r.isLittleEndian();
    
    for s in range(numSeries):
        r.setSeries(s)
        
        t = r.getSizeT()
        w = r.getSizeX()
        h = r.getSizeY()
        d = r.getSizeZ();
        c = r.getSizeC();
        
        arr = numpy.zeros((t,w,h,d,c),numpy.uint8)

        print "Time, Width, Height, Depth, Channels", t, w, h, d, c

        numImages = r.getImageCount()
        
        for i in range(numImages):
            zPos = r.getZCTCoords(i)[0]
            cPos = r.getZCTCoords(i)[1]
            tPos = r.getZCTCoords(i)[2]
            print "Images", i, "at channel", cPos , "and z-slice", zPos , "and time-point", tPos
            

            img = r.openBytes(i)

            data = numpy.array(img[0:len(img)])
            data.shape = (w,h)
            
            arr[tPos,:,:,zPos,cPos] = data
        
        seriesData.append(arr)     
    r.close()
    
    return seriesData
        
if __name__ == "__main__":
    try:
        if not jpype.isJVMStarted():
            jpype.startJVM(jpype.getDefaultJVMPath(),'-Djava.class.path=loci_tools.jar')
    except:
        print "JVM Start failed, propably it has been started already..."

    data = readLif('mausA_schnitt4.lif')
    #jpype.shutdownJVM()
    

