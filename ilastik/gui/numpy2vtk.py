from vtk import vtkImageImport

def toVtkImageData(a):
    importer = vtkImageImport()
    importer.SetDataScalarTypeToUnsignedChar()
    importer.SetDataExtent(0,a.shape[0]-1,0,a.shape[1]-1,0,a.shape[2]-1)
    importer.SetWholeExtent(0,a.shape[0]-1,0,a.shape[1]-1,0,a.shape[2]-1)
    importer.SetImportVoidPointer(a)
    importer.Update()
    return importer.GetOutput()