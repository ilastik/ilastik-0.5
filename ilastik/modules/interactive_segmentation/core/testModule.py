from ilastik.core.projectClass import Project
from ilastik.core import jobMachine
from ilastik.modules.interactive_segmentation.core.segmentors.segmentorBase import SegmentorBase
from PyQt4.QtCore import QDir
import h5py, numpy, os, shutil

from ilastik.core.testThread import setUp, tearDown

def test_InteractiveSegmentationItemModuleMgr():
    def h5equal(filename, a):
        f = h5py.File(filename, 'r')
        d = f['volume/data'].value.squeeze()
        a = a.squeeze()        
        assert a.shape == d.shape
        if a.dtype != d.dtype:
            print a.dtype, '!=', d.dtype
            assert a.dtype == d.dtype
        assert numpy.array_equal(d, a)
        return True
        
    def arrayEqual(a,b):
        assert a.shape == b.shape
        assert a.dtype == b.dtype
        if not numpy.array_equal(a,b):
            assert len(a.shape) == 3
            for x in range(a.shape[0]):
                for y in range(a.shape[1]):
                    for z in range(a.shape[2]):
                        if a[x,y,z] != b[x,y,z]:
                            print x,y,z, "a=", a[x,y,z], "b=", b[x,y,z]
            return False
        return True
    
    class FakeSegmentor(SegmentorBase):
        segmentation = None
        seeds = None
        
        segmentationGT = []
        seedsGT = []
        
        def __init__(self):
            for ver in range(3):
                seeds = numpy.zeros((120,120,120,1), dtype=numpy.uint8)
                if  ver == 0:
                    seeds[0,0,0,0] = 1
                elif ver == 1:
                    seeds[0,0,0,0] = 2
                elif ver == 2:
                    seeds[0,0,0,0] = 3
                self.seedsGT.append(seeds)
            
            for i in range(3):
                seg = numpy.ones((120,120,120,1), dtype=numpy.uint8)
                if i == 0:
                    seg[5:10,5:10,5:10,0]    = 2
                elif i == 1:
                    seg[5:30,5:20,8:17,0]    = 3
                    seg[50:70,50:70,40:60,0] = 5
                elif i == 2:
                    seg[8:12,10:30,30:40,0]  = 2
                    seg[20:30,10:30,30:40,0] = 4
                    seg[40:50,10:30,30:40,0] = 6
                self.segmentationGT.append(seg)
        
        def segment(self, labelVolume, labelValues, labelIndices):
            print "fake segment"
            assert labelVolume.shape == (120,120,120,1)
            if labelVolume[0,0,0,0] == 1:
                self.segmentation = self.segmentationGT[0]
            elif labelVolume[0,0,0,0] == 2:
                self.segmentation = self.segmentationGT[1]
            elif labelVolume[0,0,0,0] == 3:
                self.segmentation = self.segmentationGT[2]  
    
    
    # create project with some fake data
    project = Project('Project Name', 'Labeler', 'Description')
    filename = str(QDir.tempPath())+'/testdata.h5'
    f = h5py.File(filename, 'w')
    f.create_group('volume')
    f.create_dataset('volume/data', data=numpy.zeros(shape=(1,120,120,120,1), dtype=numpy.uint8))
    f.close; del f
    project.addFile([filename])
    os.remove(filename)
    
    dataMgr = project.dataMgr
    segmentor = FakeSegmentor()
    dataMgr.Interactive_Segmentation.segmentor = segmentor
    
    #initialize the module to testQDir.tempPath()+'/testdata.h5'
    s = dataMgr._activeImage.module["Interactive_Segmentation"] 
    #create outputPath, make sure it is empty
    outputPath = str(QDir.tempPath())+"/tmpseg"
    print outputPath
    if os.path.exists(outputPath):
        shutil.rmtree(outputPath)
    os.makedirs(outputPath)
    s.init()
    s.outputPath = outputPath

    shape3D = (120,120,120)
    shape4D = (120,120,120,1)
    shape5D = (1,120,120,120,1)

    version = 0

    print "*************************************************************************"
    print "* segment for the first time (version 0)                                *"
    print "*************************************************************************"
    
    s.seedLabelsVolume._data[:] = segmentor.seedsGT[version][:] #fake drawing some seeds
    s.segment() #segment
    
    assert arrayEqual(s.segmentation[0,:,:,:,:], segmentor.segmentation)
    assert not os.path.exists(s.outputPath+'/one')
    assert s._mapKeysToLabels == {}
    assert s._mapLabelsToKeys == {}
    
    #save as 'one'
    s.saveCurrentSegmentsAs('one')
    
    #we now have a 'done' overlay
    doneRef = s.done
    
    assert os.path.exists(s.outputPath)
    assert os.path.exists(s.outputPath+'/done.h5')
    assert os.path.exists(s.outputPath+'/mapping.dat')
    assert os.path.exists(s.outputPath+'/one/segmentation.h5')
    assert os.path.exists(s.outputPath+'/one/seeds.h5')
    
    h5equal(s.outputPath+'/one/segmentation.h5', segmentor.segmentation)
    h5equal(s.outputPath+'/one/seeds.h5', segmentor.seedsGT[version])
    
    assert numpy.where(s.seedLabelsVolume._data != 0) == () 
    
    doneGT = numpy.zeros(shape=shape4D, dtype=numpy.uint32)
    doneGT[numpy.where(segmentor.segmentation == 2)] = 1
    h5equal(s.outputPath+'/done.h5', doneGT)
    f = open(s.outputPath+'/mapping.dat')
    assert f.readlines() == ['1|one\r\n']
    f.close()
    
    assert s._mapKeysToLabels == {'one': set([1])}
    assert s._mapLabelsToKeys == {1: 'one'}
    assert s.segmentKeyForLabel(1) == 'one'
    assert s.segmentLabelsForKey('one') == set([1])

    s.discardCurrentSegmentation()
    assert s.segmentation == None
    assert numpy.where(s.seedLabelsVolume._data != 0) == ()

    print "*************************************************************************"
    print "* remove segment 'one'                                                  *"
    print "*************************************************************************"

    #remove segment by key
    s.removeSegmentsByKey('one')
    assert s._mapKeysToLabels == {}
    assert s._mapLabelsToKeys == {}
    assert numpy.array_equal(s.done, numpy.zeros(shape=s.done.shape, dtype=s.done.dtype))
    assert os.path.exists(s.outputPath)
    assert os.path.exists(s.outputPath+'/done.h5')
    assert os.path.exists(s.outputPath+'/mapping.dat')
    assert not os.path.exists(s.outputPath+'/one')
    f = open(s.outputPath+'/mapping.dat')
    assert f.readlines() == []
    f.close()
    
    print "*************************************************************************"
    print "* segment for the second time (version 1)                               *"
    print "*************************************************************************"
    
    version = 1
    s.seedLabelsVolume._data[:] = segmentor.seedsGT[version][:] #fake drawing some seeds
    s.segment()
    assert arrayEqual(s.segmentation[0,:,:,:,:], segmentor.segmentation)
    assert s._mapKeysToLabels == {}
    assert s._mapLabelsToKeys == {}
    
    s.saveCurrentSegmentsAs('two')
    assert os.path.exists(s.outputPath+'/two/segmentation.h5')
    assert os.path.exists(s.outputPath+'/two/seeds.h5')
    relabeledGT = segmentor.segmentation.copy()
    relabeledGT[numpy.where(relabeledGT == 1)] = 0
    relabeledGT[numpy.where(relabeledGT == 3)] = 1
    relabeledGT[numpy.where(relabeledGT == 5)] = 2
    assert arrayEqual(s.done.squeeze(), relabeledGT.squeeze().astype(numpy.uint32))
    
    assert s._mapKeysToLabels == {'two': set([1, 2])}
    assert s._mapLabelsToKeys == {1: 'two', 2: 'two'}
    
    print "*************************************************************************"
    print "* segment again (version 2)                                             *"
    print "*************************************************************************"
 
    version = 2
    s.seedLabelsVolume._data[:] = segmentor.seedsGT[version][:] #fake drawing some seeds
    s.segment()
    assert arrayEqual(s.segmentation[0,:,:,:,:], segmentor.segmentationGT[version])
    
    s.saveCurrentSegmentsAs('three')
    assert os.path.exists(s.outputPath)
    assert os.path.exists(s.outputPath+'/done.h5')
    assert os.path.exists(s.outputPath+'/mapping.dat')
    assert os.path.exists(s.outputPath+'/two/segmentation.h5')
    assert os.path.exists(s.outputPath+'/two/seeds.h5')
    assert os.path.exists(s.outputPath+'/three/segmentation.h5')
    assert os.path.exists(s.outputPath+'/three/seeds.h5')
    
    assert s._mapKeysToLabels == {'two': set([1, 2]), 'three': set([3, 4, 5])}
    assert s._mapLabelsToKeys == {1: 'two', 2: 'two', 3: 'three', 4: 'three', 5: 'three'}
    
    doneGT = numpy.zeros(shape=shape4D, dtype=numpy.uint32)
    doneGT[numpy.where(segmentor.segmentationGT[1] == 3)] = 1
    doneGT[numpy.where(segmentor.segmentationGT[1] == 5)] = 2
    doneGT[numpy.where(segmentor.segmentationGT[2] == 2)] = 3
    doneGT[numpy.where(segmentor.segmentationGT[2] == 4)] = 4
    doneGT[numpy.where(segmentor.segmentationGT[2] == 6)] = 5
    assert arrayEqual(doneGT.squeeze(), s.done.squeeze())
    
    assert h5equal(s.outputPath+'/two/segmentation.h5', segmentor.segmentationGT[1])
    assert h5equal(s.outputPath+'/three/segmentation.h5', segmentor.segmentationGT[2])
    
    print "*************************************************************************"
    print "* remove segments 'three'                                               *"
    print "*************************************************************************"
    
    s.removeSegmentsByKey('three')
    assert s._mapKeysToLabels == {'two': set([1, 2])}
    assert s._mapLabelsToKeys == {1: 'two', 2: 'two'}
    assert os.path.exists(s.outputPath)
    assert os.path.exists(s.outputPath+'/done.h5')
    assert os.path.exists(s.outputPath+'/mapping.dat')
    assert os.path.exists(s.outputPath+'/two/segmentation.h5')
    assert os.path.exists(s.outputPath+'/two/seeds.h5')
    assert not os.path.exists(s.outputPath+'/three')
    f = open(s.outputPath+'/mapping.dat')
    assert f.readlines() == ['1|two\r\n', '2|two\r\n']
    f.close()
    
    doneGT = numpy.zeros(shape=shape4D, dtype=numpy.uint32)
    doneGT[numpy.where(segmentor.segmentationGT[1] == 3)] = 1
    doneGT[numpy.where(segmentor.segmentationGT[1] == 5)] = 2
    assert arrayEqual(doneGT.squeeze(), s.done.squeeze())
    assert h5equal(s.outputPath+'/done.h5', doneGT)
    
    print "*************************************************************************"
    print "* edit segments 'two'                                                   *"
    print "*************************************************************************"
    
    s.editSegmentsByKey('two')

    print "check...."
    assert arrayEqual(s.seedLabelsVolume._data[0,:,:,:,:], segmentor.seedsGT[1])
    #assert arrayEqual(s.segmentation[0,:,:,:,:].squeeze(), segmentor.segmentation.squeeze())
    
    s.saveCurrentSegment()
    
    print "*************************************************************************"
    print "* remove segments 'two'                                                 *"
    print "*************************************************************************"
    
    s.removeSegmentsByKey('two')
    assert s._mapKeysToLabels == {}
    assert s._mapLabelsToKeys == {}
    assert os.path.exists(s.outputPath)
    assert os.path.exists(s.outputPath+'/done.h5')
    assert os.path.exists(s.outputPath+'/mapping.dat')
    assert not os.path.exists(s.outputPath+'/two')
    assert not os.path.exists(s.outputPath+'/three')
    f = open(s.outputPath+'/mapping.dat')
    assert f.readlines() == []
    f.close()
    
    doneGT = numpy.zeros(shape=shape4D, dtype=numpy.uint32)
    assert arrayEqual(doneGT.squeeze(), s.done.squeeze())
    assert h5equal(s.outputPath+'/done.h5', doneGT)
    
    #make sure that we have not overwritten the done overlay, which
    #would cause the connection with the 'Segmentation/Done' overlay
    #to break
    assert doneRef is s.done
    
    jobMachine.GLOBAL_WM.stopWorkers()