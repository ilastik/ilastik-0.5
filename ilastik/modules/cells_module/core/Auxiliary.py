# -*- coding: utf-8 -*-
from ilastik.core.baseModuleMgr import BaseModuleDataItemMgr, BaseModuleMgr

import vigra
import numpy
import h5py

from scipy import ndimage


from PyQt4.QtGui import *
from PyQt4.QtCore import *

from qimage2ndarray import rgb_view



######Auxiliary Classes#####

class Hull2DObject(object):
    def __init__(self):
        
        pass    
    
    
    def calculate(self,weights):
        self.res=numpy.zeros(weights.shape,'uint8')
        self.segmented=weights.astype(numpy.uint8)
        #finds the points onto the borders
        temp1=numpy.zeros(self.segmented[:,:].shape,'uint8')
        temp2=numpy.zeros(self.segmented[:,:].shape,'uint8')
        temp3=numpy.zeros(self.segmented[:,:].shape,'uint8')
        temp4=numpy.zeros(self.segmented[:,:].shape,'uint8')
        
        temp1[0:-1,:]=self.segmented[:,:][1:,:]
        temp2[1:,:]=self.segmented[:,:][0:-1,:]
        temp3[:,0:-1]=self.segmented[:,:][:,1:]
        temp4[:,1:]=self.segmented[:,:][:,0:-1]
        
        #Now the array contains the point onto the border
        self.res[:,:]=numpy.where(temp1+temp2+temp3+temp4==1,1,0)
        
        
        
        indeces=numpy.nonzero(self.res[:,:])
        indeces=numpy.transpose(indeces)
        
        
        
        
        #ensures that is a unstrided array
        temp=numpy.zeros(indeces.shape,'int32')
        temp[:,:]=indeces
        indeces=temp
        
        
        self.pointsHull=vigra.geometry.convexHull(indeces)
        
                
        self.mask=self.makeMask(self.pointsHull)
        
        
        
        #vigra.impex.writeVolume(self.mask*255,'mask_hull','.tif')
        
        #vigra.impex.writeVolume(msk2*255,'mask_hull','.tiff')
        
        
        CM=ndimage.measurements.center_of_mass(self.segmented[:,:])
        
        #CM=ndimage.measurements.center_of_mass(self.mask)
        
        temp=(self.mask-self.segmented)
        #vigra.impex.writeVolume(temp*255,'mask_hull','.tiff')
        
        self.res=vigra.analysis.labelImageWithBackground(temp.astype(numpy.uint8))
        
        #label of the interior region
        label=self.res[round(CM[0]),round(CM[1])]
        
        #Now the array contains only the interior
        self.res[:,:]=numpy.where(self.res==label,1,0) 

        if self.res[0,0]==1:
            print 'center of mass outside of the object!! inverting the result'
            self.res=(1-self.res)*(1)

        return self.res.astype(numpy.uint8)
    
    def makeMask(self,points):
        """this function transfor a set of points into a mask filling the polygon"""
    
        i=QImage(QSize(self.segmented.shape[0],self.segmented.shape[1]),QImage.Format_RGB32)
        p=QPainter(i)
        
        pp=QPainterPath()
        
        
        pbegin=(points[0][0],points[0][1])
        points=points[1:]
        pp.moveTo(pbegin[0],pbegin[1])
        
        for point in points:
            #print point
            pp.lineTo(point[0],point[1])
            
        pp.lineTo(pbegin[0],pbegin[1])

        pp.setFillRule(1)
        p.setPen(QPen(QColor(255, 0, 0)))
        p.setBrush(QColor(255, 0, 0))

        p.drawPath(pp)

        
        p.end()
        res=rgb_view(i)
        res=res[:,:,0]/255
        res=res.T
        return res.astype(numpy.uint8)




class PositionsDictionary3D(object):
    def __init__(self):
        """A dictionary, where the key is the point "intensity"
        (i.e. connected component number)
        and the value is a list of point coordinates [[x], [y], [z]]"""
        pass
    
    @staticmethod
    def setdict(weights):     
        objs={}
           
        nzindex=numpy.nonzero(weights.view(numpy.ndarray))
        for i in range(len(nzindex[0])):
            value = weights[nzindex[0][i], nzindex[1][i], nzindex[2][i]]
            if value > 0:
                if value not in objs:
                    objs[value] = [[], [], []]
                
                objs[value][0].append(nzindex[0][i])
                objs[value][1].append(nzindex[1][i])
                objs[value][2].append(nzindex[2][i])
    
        return objs
    

def computeDistanceMatrix(dictCenters,phySize=(1,1,1)):
    """get a dictionary of centers coordinates position and give back a relative distance matrix, not put missing value in the dict"""
    
    import numpy
    if dictCenters!={}:
        Max=max(dictCenters)
        
        coord=numpy.zeros((Max,3))
        check=0
        for k in dictCenters.iterkeys():
            if check!=k-1:
                raise
            else:
                check=check+1
            
            coord[k-1,:]=dictCenters[k]
        
        coord[:,0]=coord[:,0]*phySize[0]
        coord[:,1]=coord[:,1]*phySize[1]
        coord[:,2]=coord[:,2]*phySize[2]
            
        B=numpy.dot(coord,coord.T)
            
        A=numpy.sum(coord*coord,axis=1)
        A.shape=A.shape +(1,)
       
        A=numpy.dot(A,numpy.ones((1,A.shape[0])))
        
            
        res=numpy.sqrt(A+A.T-2*B)
    else:
        res=numpy.array([-1])
    
    return res
    
    


def saveAsOverlayed(dictCenters,segmentedGyrus,segmentedInterior,segmentedCells):
    from qimage2ndarray import rgb_view
    


if __name__ == "__main__":
    from numpy import *
    d={}
    
    print computeDistanceMatrix(d)
