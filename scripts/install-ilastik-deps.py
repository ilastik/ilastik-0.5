#!/usr/bin/env python
import __builtin__
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
__builtin__.cmake="/usr/local/bin/cmake"
__builtin__.hg="/usr/local/bin/hg"
__builtin__.git="/usr/local/git/bin/git"

__builtin__.pythonVersionPath  = installDir+"/Frameworks/Python.framework/Versions/"+pythonVersion
__builtin__.pythonBinaryPath   = pythonVersionPath+"/bin"
__builtin__.pythonSharePath    = pythonVersionPath+"/share"
__builtin__.pythonLibrary      = pythonVersionPath+"/lib/libpython"+pythonVersion+".dylib"
__builtin__.pythonExecutable   = pythonBinaryPath + "/python" + pythonVersion
__builtin__.pythonSitePackages = pythonVersionPath + "/lib/python" + pythonVersion + "/site-packages"
__builtin__.pythonIncludePath  = pythonVersionPath + "/include/python" + pythonVersion

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
os.environ["CMAKE_FRAMEWORK_PATH"] = installDir+"/Frameworks"
#Packages that use setuptools have to know where Python is installed
#see: http://stackoverflow.com/questions/3390558/installing-setuptools-in-a-private-version-of-python
os.environ["PATH"]                 = installDir+"bin:/usr/bin:/bin"
os.environ["LIBRARY_PATH"]         = installDir+"/lib"
os.environ["C_INCLUDE_PATH"]       = installDir+"/include"
os.environ["CPLUS_INCLUDE_PATH"]   = installDir+"/include"
os.environ["FRAMEWORK_PATH"]       = installDir+"/Frameworks"
os.environ["CC"]                   = gcc+" -arch x86_64"
os.environ["CXX"]                  = gpp+" -arch x86_64"
os.environ["LDFLAGS"]              = "-arch x86_64"
os.environ["BASEFLAGS"]            = "-arch x86_64"
os.environ["LDFLAGS"]              = "-L"+installDir+"/lib" + " " + "-F"+installDir+"/Frameworks"
os.environ["CPPFLAGS"]             = "-I"+installDir+"/include"
os.environ["PREFIX"]               = installDir
os.environ["MACOSX_DEPLOYMENT_TARGET"]="10.6"
os.environ['QTDIR']                = installDir
os.environ['PYTHONAPPSDIR']        = installDir + '/Applications/'

#os.environ["BINDIR"]=IHOME+"/inst/bin"
#os.environ["LIBDIR"]=IHOME+"/inst/lib"
#os.environ["DOCDIR"]=IHOME+"/inst/doc"
#os.environ["DATADIR"]=IHOME+"/inst"
#os.environ["HEADERDIR"]=IHOME+"/inst/include"
#os.environ["PLUGINDIR"]=IHOME+"/inst/plugins"
#os.environ["TRANSLATIONDIR"]=IHOME+"/inst/translations"
#os.environ["SYSCONFDIR"]=IHOME+"/inst/etc"
#os.environ["EXAMPLESDIR"]=IHOME+"/inst/examples"
#os.environ["DEMOSDIR"]=IHOME+"/inst/demos"
#os.environ["PREFIX"]=IHOME+"/inst"
#os.environ["UNUVERSALSDK"]="/Developer/SDKs/MacOSX10.4u.sdk"
#os.system("env")

from PackagesItems import *

###################################################################################################

c = sys.argv[1:]

if 'all' in c:
    c = ['jpeg', 'tiff', 'png', 'slib', 'zlib',
         'python', 'nose', 'setuptools', 'py2app',
         'hdf5',
         'numpy', 'h5py', 'boost', 'sip',
         'lis', 'vigra', 
         'qt', 'pyqt', 'qimage2ndarray',
         'pyopenglaccellerate', 'pyopengl',
         'enthoughtbase', 'traits', 'traitsgui', 'traitsbackendqt',
         'vtk',
         'fixes']

if 'jpeg' in c:
	JpegPackage()
if 'tiff' in c:
	TiffPackage()
if 'png' in c:
	PngPackage()
if 'slib' in c:
	SlibPackage()
if 'zlib' in c:
	ZlibPackage()
	
# # # # # # # # # # # # #
os.environ["PYTHONPATH"] = pythonSitePackages #installDir+"/bin:" + pythonSitePackages
os.environ["PATH"]       = os.environ["PATH"] + ':' + pythonBinaryPath

if 'python' in c:
	Python27FrameworkPackage()
	#os.system("cp -v ./inst/Frameworks/Python.framework/Versions/2.7/lib/libpython2.7.dylib ./inst/lib/libpython2.7.dylib")
if 'nose' in c:
	NosePackage()
if 'setuptools' in c:
    SetuptoolsPackage()	
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
    cmd = "cp -rv work/" + QtPackage.workdir + "/src/gui/mac/qt_menu.nib "+installDir+"/lib"
    print "Workaround #1: ", cmd
    os.system(cmd)

    cmd = "sed -i '.bkp' -e \"s|sip.setapi('QString', 2)|sip.setapi('QString', 1)|g\" "+installDir+"/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/EnthoughtBase-3.1.0-py2.7.egg/enthought/qt/__init__.py"
    print "Workaround #2: ", cmd
    os.system(cmd)
    
    cmd = "mv %s/PyQt4/uic/port_v3 %s/PyQt4/uic/_port_v3" % (pythonSitePackages, pythonSitePackages)
    print "Workaround #3: ", cmd
    os.system(cmd)
    
#if 'fixes2' in c:
#    cmd = "sed -i '.bkp' -e \"s|purelib = prefix+'/lib/python'+ver+'/site-packages'|purelib = %s|g\" work/VTK/Wrapping/Python/setup_install_paths.py" % pythonSitePackages
#    print "Workaround #4: ", cmd
#    os.system(cmd)
#    cmd = "sed -i '.bkp' -e \"s|platlib = exec_prefix+'/lib/python'+ver+'/site-packages'|platlib = %s|g\" work/VTK/Wrapping/Python/setup_install_paths.py" % pythonSitePackages
#    print "Workaround #5: ", cmd
#    os.system(cmd)