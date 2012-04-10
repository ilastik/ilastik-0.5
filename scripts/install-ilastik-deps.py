#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    Copyright 2010 L Fiaschi, T Kroeger, M Nullmeier C Sommer, C Straehle, U Koethe, FA Hamprecht. 
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

__builtin__.installDir=os.environ["HOME"]+"/ilastik-build-test"
#__builtin__.installDir = os.environ["HOME"]

__builtin__.pythonVersion="2.7"

__builtin__.gcc="gcc"
__builtin__.gpp="g++"
__builtin__.ls="/bin/ls"
__builtin__.cd="cd"
__builtin__.make="/usr/bin/make"
__builtin__.pwd="/bin/pwd"
if platform.system() == "Darwin":
  __builtin__.cmake="/usr/local/bin/cmake"
  __builtin__.hg="/usr/local/bin/hg"
  __builtin__.git="/usr/bin/git"
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
  __builtin__.pythonSitePackages = pythonVersionPath + "/lib/python" + pythonVersion
else:
  __builtin__.pythonLibrary      = pythonVersionPath+"/lib/libpython"+pythonVersion+".so"
  __builtin__.pythonSitePackages = pythonVersionPath + "/lib/python" + pythonVersion + "/site-packages"
  
__builtin__.pythonExecutable   = pythonBinaryPath + "/python" + pythonVersion
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
os.environ["PATH"]                 = installDir+"bin:"+installDir+"/Frameworks/Python.framework/Versions/2.7/bin:/usr/bin:/bin"
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
    os.environ["CC"]                   = "gcc -arch x86_64"
    os.environ["CXX"]                  = "g++ -arch x86_64"
    #see http://www.scipy.org/Installing_SciPy/Mac_OS_X
    #Quote from the above:
    #  "The default C compiler on Lion is llvm-gcc-4.2, which has so far proven to be problematic.
    #   We recommend to use gcc-4.2, or alternatively clang.
    #   The Fortran flag "-ff2c" has been reported to be necessary."
    #os.environ["FFLAGS"]               = "-ff2c"
    os.environ["LDFLAGS"]              = "-arch x86_64"
    os.environ["BASEFLAGS"]            = "-arch x86_64"
    os.environ["LDFLAGS"]              = "-L"+installDir+"/lib" + " " + "-F"+installDir+"/Frameworks"
    os.environ["CPPFLAGS"]             = "-I"+installDir+"/include"
    os.environ["MACOSX_DEPLOYMENT_TARGET"]="10.6"
    os.environ["PREFIX"] 			   += ":" + pythonBinaryPath
    os.environ["EXEC_PREFIX"] 		   = ":" + pythonBinaryPath
    #for qt4.8
    #os.environ["CXXFLAGS"]  		   ="-fvisibility=hidden"
    #os.environ["LD"]                   = "gcc-4.2 -arch x86_64"
    #os.environ["LD_LIBRARY_PATH"] = "%s/lib" % (installDir)
    #os.environ["DYLD_LIBRARY_PATH"] = "%s/lib" % (installDir)
else:
    os.environ["LD_LIBRARY_PATH"] = "%s/lib" % (installDir)
###################################################################################################

all = ['zlib', 'slib', 
	'fftw3f', 'fftw3', 'jpeg', 'tiff', 'png',
	'setuptools','nose', 'py2app',
    'hdf5',
     ########## 'sip',
    'lis'
    #'fixes'
    ]

all_mac = ['readline', 'gdbm', 'python', 'zlib', 'slib', 
	'fftw3f', 'fftw3', 'jpeg', 'tiff', 'png',
	'setuptools','nose', 'py2app',
    'hdf5',
    'numpy', 'h5py', 'boost', 'sip',
    'lis', 'vigra', 
    'qt', 'pyqt', 'qimage2ndarray',
    'vtk',
    'greenlet',
    'blist',
    'psutil',
    #'fixes'
    ]

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

for p in c:
        
	if 'readline' == p:
		ReadlinePackage()
	elif 'gdbm'  == p:
		GdbmPackage()
	elif 'ipython'  == p:
		ipythonPackage()
	elif 'zlib'  == p:
	    ZlibPackage()
	elif 'slib'  == p:
		SlibPackage()
	elif 'fftw3f'  == p:
		FFTW3F()
	elif 'fftw3'  == p:
		FFTW3()
	elif 'jpeg'  == p:
		JpegPackage()
	elif 'tiff'  == p:
		TiffPackage()
	elif 'png'  == p:
		PngPackage()
	
    # # # # # # # # # # # # #
	os.environ["PYTHONPATH"] = pythonSitePackages #installDir+"/bin:" + pythonSitePackages
	# /Users/opetra/ilastik-build/Frameworks/Python.framework/Versions/2.7/lib//python2.7/
	#add python binaries to system search path, make sure they are found before /usr/bin and /bin
	os.environ["PATH"]       = pythonBinaryPath + ":" + os.environ["PATH"]

	if 'env'  == p:
		for k,v in os.environ.iteritems():
			print k,v
			
	elif 'python'  == p:
		PythonPackage()
	elif 'setuptools'  == p:
		SetuptoolsPackage()
	elif 'nose'  == p:
		NosePackage()
	if platform.system() == "Darwin":
		if 'py2app'  == p:
			Py2appPackage()

# # # # # # # # # # # # #
	
	if 'hdf5'  == p:
		Hdf5Package()

# # # # # # # # # # # # #

	elif 'numpy'  == p:
		NumpyPackage()
	elif 'h5py'  == p:
		H5pyPackage()
	elif 'boost'  == p:
		BoostPackage()
	elif 'sip'  == p:
		SipPackage()

# # # # # # # # # # # # #	
	
	elif 'lis'  == p:
		LISPackage()
	elif 'vigra'  == p:
		##############################################CStraehlePackage()
		VigraPackage()
    
# # # # # # # # # # # # #

	elif 'qt'  == p:
		QtPackage()
	elif 'pyqt'  == p:
		PyQtPackage()
	elif 'qimage2ndarray'  == p:
		Qimage2ndarrayPackage()
	
# # # # # # # # # # # # #

	elif 'pyopenglaccellerate'  == p:
		PyOpenGLAccelleratePackage()#
	elif 'pyopengl'  == p:
		PyOpenGLPackage()

# # # # # # # # # # # # #

	elif 'enthoughtbase'  == p:
		EnthoughtBasePackage()
	elif 'traits'  == p:
		TraitsPackage()
	elif 'traitsgui'  == p:
		TraitsGUIPackage()
	elif 'traitsbackendqt'  == p:
		TraitsBackendQtPackage()

# # # # # # # # # # # # #

	elif 'vtk'  == p:
		VTKGitPackage()

# # # # # # # # # # # # #
#New Stuff for the Graph


	elif "greenlet"  == p:
		GreenletPackage()
	elif "psutil"  == p:
		PsutilPackage()
	elif "blist"  == p:
		BlistPackage()
    



#########################
	elif "drtile"  == p:
		cmd = """ %s /Users/opetra/hci/repositories/lazyflow/lazyflow/drtile
		""" % (cmake)
		os.system(cmd)
'''	
	elif ('fixes'  == p) and ('download' not in sys.argv[0]):
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
'''
#    else:
#    	raise RuntimeError('=> 'p, ' <= Package does not exist')
