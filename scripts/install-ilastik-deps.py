#!/usr/bin/env python
# -*- coding: utf-8 -*-
import __builtin__
import platform
import urllib2, os, sys, tarfile, shutil
from hashlib import md5

__builtin__.installDir="/ilastik"
__builtin__.pythonVersion="2.7"

__builtin__.gcc="/usr/bin/gcc"
__builtin__.gpp="/usr/bin/g++"
__builtin__.ls="/bin/ls"
__builtin__.cd="cd"
__builtin__.make="/usr/bin/make"
__builtin__.pwd="/bin/pwd"
if platform.system() == "Darwin":
  __builtin__.cmake="/usr/local/bin/cmake"
  __builtin__.hg="/usr/local/bin/hg"
  __builtin__.git="/usr/local/git/bin/git"
else:
  __builtin__.cmake="/usr/bin/cmake"
  __builtin__.hg="/usr/bin/hg"
  __builtin__.git="/usr/bin/git"

if platform.system() == "Darwin":
  __builtin__.pythonVersionPath  = installDir+"/Frameworks/Python.framework/Versions/"+pythonVersion
else:
  __builtin__.pythonVersionPath  = installDir 
__builtin__.pythonBinaryPath   = pythonVersionPath+"/bin"
__builtin__.pythonSharePath    = pythonVersionPath+"/share"
if platform.system() == "Darwin":
  __builtin__.pythonLibrary      = pythonVersionPath+"/lib/libpython"+pythonVersion+".dylib"
else:
  __builtin__.pythonLibrary      = pythonVersionPath+"/lib/libpython"+pythonVersion+".so"
__builtin__.pythonExecutable   = pythonBinaryPath + "/python" + pythonVersion
__builtin__.pythonSitePackages = pythonVersionPath + "/lib/python" + pythonVersion + "/site-packages"
__builtin__.pythonIncludePath  = pythonVersionPath + "/include/python" + pythonVersion

from PackagesItems import *

# Create the initial structure of the project ######################################################

def mkdir(dir):
	if not os.path.exists(dir):
		os.makedirs(dir)

mkdir('distfiles')
mkdir('work')
mkdir(installDir)
mkdir(installDir+'/lib')
mkdir(installDir+'/bin')
mkdir(installDir+'/include')
mkdir(installDir+'/Frameworks')

###################################################################################################

#IHOME=os.getcwd()
#print "Setting IHOME to" + IHOME
#os.environ["IHOME"]=IHOME

os.environ["CMAKE_PREFIX_PATH"]    = installDir
os.environ["CMAKE_INSTALL_PREFIX"] = installDir
os.environ["CMAKE_INCLUDE_PATH"]   = installDir+"/include"
os.environ["CMAKE_LIBRARY_PATH"]   = installDir+"/lib"
os.environ["PATH"]                 = installDir+"bin:/usr/bin:/bin"
os.environ["LIBRARY_PATH"]         = installDir+"/lib"
os.environ["C_INCLUDE_PATH"]       = installDir+"/include"
os.environ["CPLUS_INCLUDE_PATH"]   = installDir+"/include"
os.environ["PREFIX"]               = installDir
os.environ['QTDIR']                = installDir
os.environ['PYTHONAPPSDIR']        = installDir + '/Applications/'

if platform.system() == "Darwin":
    os.environ["CMAKE_FRAMEWORK_PATH"] = installDir+"/Frameworks"
    #Packages that use setuptools have to know where Python is installed
    #see: http://stackoverflow.com/questions/3390558/installing-setuptools-in-a-private-version-of-python
    os.environ["FRAMEWORK_PATH"]       = installDir+"/Frameworks"
    os.environ["CC"]                   = gcc+" -arch x86_64"
    os.environ["CXX"]                  = gpp+" -arch x86_64"
    os.environ["LDFLAGS"]              = "-arch x86_64"
    os.environ["BASEFLAGS"]            = "-arch x86_64"
    os.environ["LDFLAGS"]              = "-L"+installDir+"/lib" + " " + "-F"+installDir+"/Frameworks"
    os.environ["CPPFLAGS"]             = "-I"+installDir+"/include"
    os.environ["MACOSX_DEPLOYMENT_TARGET"]="10.6"
else:
    os.environ["LD_LIBRARY_PATH"] = "%s/lib" % (installDir,)
###################################################################################################

all = ['jpeg', 'tiff', 'png', 'slib', 'zlib',
    'python', 'nose', 'setuptools',
    'hdf5',
    'numpy', 'h5py', 'boost', 'sip',
    'lis', 'vigra', 
    'qt', 'pyqt', 'qimage2ndarray',
    'pyopenglaccellerate', 'pyopengl',
    'enthoughtbase', 'traits', 'traitsgui', 'traitsbackendqt',
    'vtk',
    'fixes']
if platform.system() == "Darwin":
    all.append('py2app')

c = sys.argv[1:]

if 'all' in c:
    c = all

if 'from' in c:
    startpackage=c[1]
    try:
        index=all.index(startpackage)
    except:
        raise RuntimeError('package ' + startpackage + 'not known')
        
    for i in range(index,len(all)):
        print all[i]
        c.append(all[i])
    
if 'jpeg' in c:
	JpegPackage()
if 'tiff' in c:
	TiffPackage()
if 'zlib' in c:
    ZlibPackage()
if 'png' in c:
	PngPackage()
if 'slib' in c:
	SlibPackage()
	
# # # # # # # # # # # # #
os.environ["PYTHONPATH"] = pythonSitePackages #installDir+"/bin:" + pythonSitePackages
os.environ["PATH"]       = os.environ["PATH"] + ':' + pythonBinaryPath

if 'python' in c:
	PythonPackage()
if 'nose' in c:
	NosePackage()
if 'setuptools' in c:
    SetuptoolsPackage()
if platform.system() == "Darwin":
    if 'py2app' in c:
        Py2appPackage()

# # # # # # # # # # # # #
	
if 'hdf5' in c:
	Hdf5Package()

# # # # # # # # # # # # #

if 'numpy' in c:
	NumpyPackage()
if 'h5py' in c:
	H5pyPackage()
if 'boost' in c:
	BoostPackage()
if 'sip' in c:
	SipPackage()

# # # # # # # # # # # # #	
	
if 'lis' in c:
    LISPackage()
if 'vigra' in c:
    CStraehlePackage()
    VigraPackage()
    
# # # # # # # # # # # # #

if 'qt' in c:
	QtPackage()
if 'pyqt' in c:
	PyQtPackage()
if 'qimage2ndarray' in c:
	Qimage2ndarrayPackage()
	
# # # # # # # # # # # # #

if 'pyopenglaccellerate' in c:
	PyOpenGLAccelleratePackage()#
if 'pyopengl' in c:
	PyOpenGLPackage()

# # # # # # # # # # # # #

if 'enthoughtbase' in c:
	EnthoughtBasePackage()
if 'traits' in c:
	TraitsPackage()
if 'traitsgui' in c:
	TraitsGUIPackage()
if 'traitsbackendqt' in c:
	TraitsBackendQtPackage()

# # # # # # # # # # # # #

if 'vtk' in c:
	VTKGitPackage()

# # # # # # # # # # # # #

if 'fixes' in c:
    if platform.system() == "Darwin":
        cmd = "cp -rv work/" + QtPackage.workdir + "/src/gui/mac/qt_menu.nib "+installDir+"/lib"
        print "Workaround #1: ", cmd
        os.system(cmd)
    
    cmd = "mv %s/PyQt4/uic/port_v3 %s/PyQt4/uic/_port_v3" % (pythonSitePackages, pythonSitePackages)
    print "Workaround #2: ", cmd
    os.system(cmd)
    
    cmd = "cp -rv work/vigra/vigranumpy/src/core/vigranumpycore.so "+installDir+"/lib"
    print "Workaround #3: ", cmd
    os.system(cmd)    
