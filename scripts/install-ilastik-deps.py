#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    Copyright 2010 L Fiaschi, T Kroeger, M Nullmaier C Sommer, C Straehle, U Koethe, FA Hamprecht. 
#    All rights reserved.
#    
#    Redistribution and use in source and binary forms, with or without modification, are
#    permitted provided that the following conditions are met:
#    
#       1. Redistributions of source code must retain the above copyright notice, this list of
#          conditions and the following disclaimer.
#    
#       2. Redistributions in binary form must reproduce the above copyright notice, this list
#          of conditions and the following disclaimer in the documentation and/or other materials
#          provided with the distribution.
#    
#    THIS SOFTWARE IS PROVIDED BY THE ABOVE COPYRIGHT HOLDERS ``AS IS'' AND ANY EXPRESS OR IMPLIED
#    WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
#    FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE ABOVE COPYRIGHT HOLDERS OR
#    CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#    CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#    SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
#    ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#    NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
#    ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#    
#    The views and conclusions contained in the software and documentation are those of the
#    authors and should not be interpreted as representing official policies, either expressed
#    or implied, of their employers.



import __builtin__
import platform
import urllib2, os, sys, tarfile, shutil
from hashlib import md5

####__builtin__.installDir="/ilastik"
__builtin__.installDir = os.environ["HOME"]

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

all = ['fftw3f', 'fftw3', 'jpeg', 'tiff', 'zlib','png', 'slib',
    'python', 'nose', 'setuptools', 'py2app',
    'hdf5',
    'numpy', 'h5py', 'boost', 'sip',
    'lis', 'vigra', 
    'qt', 'pyqt', 'qimage2ndarray',
    'pyopenglaccellerate', 'pyopengl',
    'enthoughtbase', 'traits', 'traitsgui', 'traitsbackendqt',
    'vtk',
    'greenlet',
    'psutil',
    'fixes']

#if platform.system() == "Darwin":
#    all.append('py2app')

c = sys.argv[1:]

if 'all' in c:
    c = all
    #os.system("rm -rf " + installDir + "/*")


if 'from' in c:
    startpackage=c[1]
    try:
        index=all.index(startpackage)
    except:
        raise RuntimeError('package ' + startpackage + 'not known')
        
    for i in range(index,len(all)):
        print all[i]
        c.append(all[i])
 
if 'fftw3f' in c:
	FFTW3F()
if 'fftw3' in c:
	FFTW3()
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
    ##############################################CStraehlePackage()
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
#New Stuff for the Graph


if "greenlet" in c:
    GreenletPackage()

if "psutil" in c:
    PsutilPackage()
    



#########################

if ('fixes' in c) and ('download' not in sys.argv[0]):
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
