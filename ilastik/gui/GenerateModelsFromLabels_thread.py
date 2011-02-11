from vtk import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from functools import partial

import sys, h5py, copy
from numpy2vtk import toVtkImageData

#make the program quit on Ctrl+C
import signal, numpy
signal.signal(signal.SIGINT, signal.SIG_DFL)

#Read
#http://www.vtk.org/pipermail/vtkusers/2010-July/110094.html
#for information on why not to inherit from QThread
class MeshExtractor(QObject):
    inputImage = None
    numpyVolume = None
    meshes = dict()
    elapsed = QElapsedTimer()
    suppressedLabels = list()
    
    skipped = 0
    emitted = 0
    
    def __init__(self, parent=None):
        QObject.__init__(self, parent)
    
    def progressCallback(self, caller, eventId):
        self.maybeEmitProgress(caller.GetProgress())
    
    def maybeEmitProgress(self, progress):
        if self.elapsed.elapsed() > 100:
            self.emit(SIGNAL("currentStepProgressChanged"), progress)
            self.elapsed.restart()
            self.emitted +=1
        else:
            self.skipped +=1
    
    def SetInput(self, numpyVolume):
        self.numpyVolume = numpyVolume.copy()
    def SuppressLabels(self, labelList):
        self.suppressedLabels = labelList
    
    @pyqtSignature("run()")
    def run(self):
        self.elapsed.restart()
        count = 0
        
        if self.numpyVolume is None:
            raise RuntimeError("You need to call SetInput() first")
   
        print "numpyVolume has shape =", self.numpyVolume.shape, self.numpyVolume.dtype
   
        self.inputImage = toVtkImageData(self.numpyVolume)
   
        #Create all of the classes we will need   
        histogram     = vtkImageAccumulate()
        discreteCubes = vtkDiscreteMarchingCubes()
        smoother      = vtkWindowedSincPolyDataFilter()
        selector      = vtkThreshold()
        scalarsOff    = vtkMaskFields()
        geometry      = vtkGeometryFilter()
        #writer        = vtkXMLPolyDataWriter()

        #Define all of the variables
        startLabel          = 0
        endLabel            = numpy.max(self.numpyVolume[:])
        filePrefix          = 'label'
        smoothingIterations = 15
        passBand            = 0.001
        featureAngle        = 120.0

        #Generate models from labels
        #1) Read the meta file
        #2) Generate a histogram of the labels
        #3) Generate models from the labeled volume
        #4) Smooth the models
        #5) Output each model into a separate file

        self.emit(SIGNAL("newStep"), "Histogram")
        qDebug("*** Histogram ***")
        histogram.SetInput(self.inputImage)
        histogram.AddObserver(vtkCommand.ProgressEvent, self.progressCallback)
        histogram.SetComponentExtent(0, endLabel, 0, 0, 0, 0)
        histogram.SetComponentOrigin(0, 0, 0)
        histogram.SetComponentSpacing(1, 1, 1)
        histogram.Update()

        self.emit(SIGNAL("newStep"), "Marching Cubes")
        qDebug("*** Marching Cubes ***")
        discreteCubes.SetInput(self.inputImage)
        discreteCubes.AddObserver(vtkCommand.ProgressEvent, self.progressCallback)
        discreteCubes.GenerateValues(endLabel - startLabel + 1, startLabel, endLabel)

        self.emit(SIGNAL("newStep"), "Smoothing")
        qDebug("*** Smoothing ***")
        smoother.SetInput(discreteCubes.GetOutput())
        smoother.AddObserver(vtkCommand.ProgressEvent, self.progressCallback)
        smoother.SetNumberOfIterations(smoothingIterations)
        smoother.BoundarySmoothingOff()
        smoother.FeatureEdgeSmoothingOff()
        smoother.SetFeatureAngle(featureAngle)
        smoother.SetPassBand(passBand)
        smoother.NonManifoldSmoothingOn()
        smoother.NormalizeCoordinatesOn()
        smoother.Update()

        self.emit(SIGNAL("newStep"), "Preparing meshes")
        qDebug("*** Preparing meshes ***")
        selector.SetInput(smoother.GetOutput())
        selector.SetInputArrayToProcess(0, 0, 0,
                                        vtkDataObject.FIELD_ASSOCIATION_CELLS,
                                        vtkDataSetAttributes.SCALARS)

        #Strip the scalars from the output
        scalarsOff.SetInput(selector.GetOutput())
        scalarsOff.CopyAttributeOff(vtkMaskFields.POINT_DATA,
                                    vtkDataSetAttributes.SCALARS)
        scalarsOff.CopyAttributeOff(vtkMaskFields.CELL_DATA,
                                    vtkDataSetAttributes.SCALARS)

        geometry.SetInput(scalarsOff.GetOutput())

        #writer.SetInput(geometry.GetOutput())
        
        selector.ThresholdBetween(2, 2)
        
        self.emit(SIGNAL("newStep"), "Writing meshes")
        qDebug("*** Writing meshes ***")
        for i in range(startLabel, endLabel+1):
            self.maybeEmitProgress((i-startLabel+1)/float(endLabel-startLabel+1))
            
            if i in self.suppressedLabels:
                continue
            
            #print "elapsed since: ",t.elapsed()
            #count +=1
            #print count
            
            #see if the label exists, if not skip it
            frequency = histogram.GetOutput().GetPointData().GetScalars().GetTuple1(i)
            if frequency == 0.0:
                continue

            qDebug("%d " % (i))
            #select the cells for a given label
            selector.ThresholdBetween(i, i)
            selector.Update()

            #print "BLAAH"
            #print geometry.GetOutput().GetNumberOfCells()
            #print geometry.GetOutput().GetNumberOfPieces()
            #print geometry.GetOutput().GetNumberOfPoints()
            #print geometry.GetOutput().GetNumberOfPieces()
            #print geometry.GetOutput().GetNumberOfPolys()
            #print geometry.GetOutput().GetNumberOfVerts()
            #print geometry.GetOutput().GetNumberOfStrips()
            #print geometry.GetOutput().GetPiece()
            #print geometry.GetOutput().GetMaxCellSize()

            #print geometry.GetOutput()
            
            #this seems to be a bug in VTK, why should this call be necessary?
            geometry.GetOutput().Update()
            poly = vtkPolyData()
            poly.DeepCopy(geometry.GetOutput())
            self.meshes[i] = poly

            """
            #output the polydata
            fileName = "%s%d.vtp" % (filePrefix, i)
            #print "%s writing %s" % (sys.argv[0], fileName)
            writer.SetFileName(fileName)
            writer.Write()
            """
        print "MeshExtractor::done"
        self.emit(SIGNAL('done()'))

class MeshExtractorDialog(QDialog):
    currentStep = 0
    
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        
        #w = QWidget()
        #self.setCentralWidget(w)
        
        l = QVBoxLayout()
        self.setLayout(l)
        
        self.overallProgress = QProgressBar()
        self.overallProgress.setRange(0, 5)
        self.overallProgress.setFormat("step %v of 5")
        
        self.currentStepProgress = QProgressBar()
        self.currentStepProgress.setRange(0, 100)
        self.currentStepProgress.setFormat("%p %")
        
        self.overallLabel = QLabel("Overall progress")
        self.currentStepLabel = QLabel("Current step")
        
        l.addWidget(self.overallLabel)
        l.addWidget(self.overallProgress)
        l.addWidget(self.currentStepLabel)
        l.addWidget(self.currentStepProgress)
        
        self.update()

    def onNewStep(self, description):
        #print "*** new step: %s" % (description)
        self.currentStep += 1
        self.currentStepProgress.setValue(0)
        self.overallProgress.setValue(self.currentStep)
        self.currentStepLabel.setText(description)
        self.update()

    def onCurrentStepProgressChanged(self, progress):
        #print " ", progress
        self.currentStepProgress.setValue( round(100.0*progress) )
        self.update()

    def run(self, segVolume, suppressedLabels=()):
        self.thread = QThread(self)
        self.extractor = MeshExtractor(None)
        self.extractor.SetInput(segVolume)
        self.extractor.SuppressLabels(suppressedLabels)
        #m.start()
        self.connect(self.extractor, SIGNAL("newStep"), self.onNewStep)#, Qt.BlockingQueuedConnection)
        self.connect(self.extractor, SIGNAL("currentStepProgressChanged"), self.onCurrentStepProgressChanged)#, Qt.BlockingQueuedConnection)
        print "running in thread"

        self.extractor.moveToThread(self.thread)
        self.connect(self.extractor, SIGNAL('done()'), self.thread.quit)
        self.connect(self.thread, SIGNAL('finished()'), self.onMeshesExtracted)

        self.thread.start()
        QMetaObject.invokeMethod(self.extractor, 'run')

    def onMeshesExtracted(self):
        print 'MeshExtractorDialog::onMeshesExtracted'
        print self.extractor.meshes.keys()
        
        print "print self.thread.isRunning() = ", self.thread.isRunning()
        
        print self.extractor.skipped, self.extractor.emitted
        
        self.emit(SIGNAL('done()'))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    f=h5py.File("/home/thorben/phd/src/vtkqt-test/seg.h5")
    seg=f['volume/data'][0,:,:,:,0]
    f.close()

    window = MeshExtractorDialog()
    window.show()
    QTimer.singleShot(200, partial(window.run, seg));
    app.exec_()

