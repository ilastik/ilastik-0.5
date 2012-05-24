#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    Copyright 2011 L Fiaschi, T Kroeger, M Nullmeier, C Sommer, C Straehle, U Koethe, FA Hamprecht. 
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
from PackagesBase import Package
import os, platform
import urllib2, os, tarfile, shutil
import multiprocessing
        

###################################################################################################

class FFTW3(Package):
    src_uri = 'http://fftw.org/fftw-3.2.2.tar.gz'
    correctMD5sum = 'b616e5c91218cc778b5aa735fefb61ae'
    workdir = 'fftw-3.2.2'
    
    def conf_all(self):
        return " --enable-shared --enable-portable-binary --disable-fortran --prefix=" + self.prefix

    def configure_darwin(self):
        return "./configure --disable-dependency-tracking --enable-static=no " + self.conf_all()

    def configure_linux(self):
        return "./configure "  + self.conf_all()

###################################################################################################

class FFTW3F(Package):
    src_uri = 'http://fftw.org/fftw-3.2.2.tar.gz'
    correctMD5sum = 'b616e5c91218cc778b5aa735fefb61ae'
    workdir = 'fftw-3.2.2'

    def conf_all(self):
        return " --enable-single --enable-shared --enable-portable-binary --disable-fortran --prefix=" + self.prefix

    def configure_darwin(self):
        return "./configure --disable-dependency-tracking --enable-static=no " + self.conf_all()

    def configure_linux(self):
        return "./configure "  + self.conf_all()

###################################################################################################

class JpegPackage(Package):
    src_uri = 'http://www.ijg.org/files/jpegsrc.v8c.tar.gz'
    workdir = 'jpeg-8c'
    
    def configure_darwin(self):
        return "./configure --disable-dependency-tracking --enable-static=no --prefix=" + self.prefix

    def configure_linux(self):
        return "./configure  --prefix=" + self.prefix

###################################################################################################

class TiffPackage(Package):
    src_uri = 'http://download.osgeo.org/libtiff/tiff-3.9.4.tar.gz'
    workdir ='tiff-3.9.4'
    
    def configure_darwin(self):
        return """./configure --enable-static=no \\
                             --disable-dependency-tracking \\
                             --with-apple-opengl-framework \\
                             --prefix=%s""" % self.prefix

    def configure_linux(self):
        return """./configure --prefix=%s""" % self.prefix

###################################################################################

class PngPackage(Package):
    src_uri = 'ftp://ftp.simplesystems.org/pub/libpng/png/src/libpng-1.4.11.tar.gz'
    workdir = 'libpng-1.4.11'
    
    def configure_darwin(self):
        return """./configure --disable-dependency-tracking \\
                             --enable-static=no \\
                             --prefix=%s""" % self.prefix

    def configure_linux(self):
        return """./configure --enable-static=no \\
                             --prefix=%s""" % self.prefix
###################################################################################################        

class SlibPackage(Package):
    src_uri='http://www.hdfgroup.org/ftp/lib-external/szip/2.1/src/szip-2.1.tar.gz'
    workdir = 'szip-2.1'
    
    def configure_darwin(self):
        return """./configure --disable-dependency-tracking \\
                           --enable-static=no \\
                           --prefix=%s""" % self.prefix

    def configure_linux(self):
        return """./configure --enable-static=no \\
                           --prefix=%s""" % self.prefix
###################################################################################################
        
class ZlibPackage(Package):
    src_uri = 'http://zlib.net/zlib-1.2.7.tar.gz'
    workdir = 'zlib-1.2.7'
    
    def unpack(self):
        Package.unpack(self)
    
    def configure_darwin(self):
        return """./configure --64 \\
                              --prefix='%s'"""  % self.prefix

    def configure_linux(self):
        return """./configure --64 \\
                              --prefix='%s'"""  % self.prefix
###################################################################################################

class Hdf5Package(Package):
    src_uri = 'http://www.hdfgroup.org/ftp/HDF5/current/src/hdf5-1.8.8.tar.gz'
    #correctMD5sum = 'df131d156634608e4a7bf26baeafc940'
    workdir ='hdf5-1.8.8'
    
    def unpack(self):
        Package.unpack(self)

    def configure_darwin(self):
        return """./configure --disable-dependency-tracking \\
                             --enable-static=no \\
                             --prefix='%s'""" % self.prefix

    def configure_linux(self):
        return """./configure --enable-static=no \\
                              --prefix='%s'""" % self.prefix

###################################################################################################

class BoostPackage(Package):
    src_uri = 'http://downloads.sourceforge.net/project/boost/boost/1.45.0/boost_1_45_0.tar.bz2'
    workdir = 'boost_1_45_0'
    
    #def unpack(self):
    #    pass
    
    def configure(self):
        #Package.configure(self)
        if platform.system() == "Darwin":
            self.oldCC  =  os.environ["CC"]
            self.oldCXX =  os.environ["CXX"]
            os.environ["CC"]  = gcc#+" -arch x86_64"
            os.environ["CXX"] = gpp#+" -arch x86_64"
        cmd = """./bootstrap.sh --prefix=%s \\
                                --with-python=%s \\
                                --with-libraries=python""" % (self.prefix, pythonExecutable)
        self.system(cmd)
        if platform.system() == "Darwin":
            os.environ["CC"]  = self.oldCC
            os.environ["CXX"] = self.oldCXX

    def make(self):
        pass
    
    def makeInstall(self):
        self.system("./bjam install --prefix=%s" % self.prefix)

################################################################################

class PythonPackage(Package):
    src_uri = 'http://www.python.org/ftp/python/2.7.1/Python-2.7.1.tar.bz2'
    workdir = 'Python-2.7.1'
    #patches=['patch-Mac-PythonLauncher-Makefile.in.diff']
    
    def unpack(self):
        Package.unpack(self)
    
    def configure_darwin(self):
        return """DESTDIR=%s \\
                 ./configure --prefix=%s \\
                             --enable-framework=%s/Frameworks \\
               """ % (self.prefix,self.prefix,self.prefix)

    def configure_linux(self):
        return "DESTDIR=%s ./configure --prefix=%s --enable-shared" \
                % (self.prefix,self.prefix)

    def make(self):
        if platform.system() == 'Darwin':
            self.system("find . -name Makefile | xargs -n1 sed -i '.bkp' -e \"s|PYTHONAPPSDIR=/Applications/|PYTHONAPPSDIR=%s/Applications/|g\"" %  self.prefix)
     	self.system("make DESTDIR=%s" % self.prefix)
     	
    def makeInstall(self):
        self.system("make install DESTDIR=''")
    
##################################################################################

class NosePackage(Package):
    src_uri ='http://pkgs.fedoraproject.org/repo/pkgs/python-nose/nose-1.0.0.tar.gz/9542d4c66e04880d8144990de76e0b88/nose-1.0.0.tar.gz'
    workdir = 'nose-1.0.0'
    
    def unpack(self):
        Package.unpack(self)
    def configure(self):
        pass
    def make(self):        
        pass
    def makeInstall(self):
        self.system(pythonExecutable+" setup.py install")

###################################################################################################

class NumpyPackage(Package):
    src_uri = 'http://sourceforge.net/projects/numpy/files/NumPy/1.5.1/numpy-1.5.1.tar.gz'
    workdir = 'numpy-1.5.1'
    
    def configure(self):
        pass
 
    def make(self):        
        self.system(pythonExecutable+" setup.py build")
    
    def makeInstall(self):
        self.system(pythonExecutable+" setup.py install")

######################################################################################        

class QtPackage(Package):
    src_uri = 'http://get.qt.nokia.com/qt/source/qt-everywhere-opensource-src-4.7.2.tar.gz'
    correctMD5sum = '66b992f5c21145df08c99d21847f4fdb'
    workdir = 'qt-everywhere-opensource-src-4.7.2'
    patches = ['qtbug-15370.patch']
    
    def unpack(self):
        Package.unpack(self)
    
    def configure(self):
        macosxspecial = """ -no-framework \\
        -no-sse3 -no-sse4.1 -no-sse4.2 -no-ssse3 -no-dwarf2 \\
        """
        
        if platform.system() != "Darwin":
            macosxspecial = ""

        
        cmd = """echo 'yes' | ./configure %s \\
        -opensource \\
        -arch x86_64 \\
        -optimized-qmake\\
        -nomake examples\\
        -nomake demos\\
        -nomake docs\\
        -nomake translations\\
        -nomake tools\\
        -no-multimedia -no-xmlpatterns -no-svg -no-audio-backend -no-phonon -no-phonon-backend -no-svg -no-webkit\\
        -no-openssl\\
        -no-declarative -no-declarative-debug\\
        -no-script -no-scripttools -no-javascript-jit\\
        -no-sql-sqlite -no-sql-sqlite2 -no-sql-psql -no-sql-db2 -no-sql-ibase -no-sql-mysql -no-sql-oci\\
        -no-sql-odbc -no-sql-sqlite_symbian -no-sql-tds\\
        -no-pch\\
        -no-dbus\\
        -no-cups\\
        -no-nis\\
        -qt-libpng\\
        -fast -release -shared -no-accessibility\\
        --prefix=%s""" % (macosxspecial,self.prefix,)
        self.system(cmd)
        
    def make(self, parallel = multiprocessing.cpu_count()):
        self.system(make + " -j" + str(parallel))
        
        #Also install Designer, which is needed by VTK
        self.system(("cd tools/designer && ../../bin/qmake && %s -j"
                     + str(parallel) + " && %s install")
                    % (make, make))
        
###########################################################################################################

class PyQtPackage(Package):
    src_uri = "http://pkgs.fedoraproject.org/repo/pkgs/PyQt4/PyQt-x11-gpl-4.8.4.tar.gz/97c5dc1042feb5b3fe20baabad055af1/PyQt-x11-gpl-4.8.4.tar.gz"
    correctMD5sum = '97c5dc1042feb5b3fe20baabad055af1'
    workdir = 'PyQt-x11-gpl-4.8.4'

    def configure_darwin(self):
        return """%s configure.py \\
        --confirm-license \\
        --no-designer-plugin \\
        -q %s/bin/qmake \\
        --use-arch=x86_64""" % (pythonExecutable, self.prefix)

    def configure_linux(self):
        return """%s configure.py \\
        --confirm-license \\
        --no-designer-plugin \\
        -q %s/bin/qmake """ % (pythonExecutable, self.prefix)

##########################################################################################################

class SipPackage(Package):
    src_uri = 'http://pkgs.fedoraproject.org/repo/pkgs/sip/sip-4.12.3.tar.gz/d0f1fa60494db04b4d115d4c2d92f79e/sip-4.12.3.tar.gz'
    correctMD5sum = 'd0f1fa60494db04b4d115d4c2d92f79e'
    workdir = 'sip-4.12.3'
    
    def configure_darwin(self):
        return pythonExecutable+" configure.py --arch=x86_64 -s MacOSX10.6.sdk" # +self.prefix + "/include/sip "
    
    def configure_linux(self):
        return pythonExecutable+" configure.py" # +self.prefix + "/include/sip "

############################################################################################################

class H5pyPackage(Package):
    src_uri = 'http://h5py.googlecode.com/files/h5py-1.3.1.tar.gz'
    
    workdir = 'h5py-1.3.1'
    
    def configure(self):
        cmd = pythonExecutable+" setup.py configure --hdf5=" + self.prefix
        self.system(cmd)
    
    def make(self):
        cmd = pythonExecutable+" setup.py build"
        self.system(cmd)
        
    def makeInstall(self):
        cmd = pythonExecutable+" setup.py install"
        self.system(cmd)
#############################################################################################################

class GreenletPackage(Package):
    src_uri = 'http://pypi.python.org/packages/source/g/greenlet/greenlet-0.3.1.tar.gz'
    correctMD5sum = '8d75d7f3f659e915e286e1b0fa0e1c4d'
    workdir = 'greenlet-0.3.1'
    
    def configure(self):
        pass
    
    def make(self):
        cmd = pythonExecutable+" setup.py build"
        self.system(cmd)
        
    def makeInstall(self):
        cmd = pythonExecutable+" setup.py install"
        self.system(cmd)
        
#############################################################################################################
class PsutilPackage(Package):
    src_uri = 'http://psutil.googlecode.com/files/psutil-0.4.1.tar.gz'
    
    workdir = 'psutil-0.4.1'
    
    def configure(self):
        pass
    
    def make(self):
        cmd = pythonExecutable+" setup.py build"
        self.system(cmd)
        
    def makeInstall(self):
        cmd = pythonExecutable+" setup.py install"
        self.system(cmd)
  

    



##############################################################################################################

class PyOpenGLAccelleratePackage(Package):
    src_uri = 'http://pypi.python.org/packages/source/P/PyOpenGL-accelerate/PyOpenGL-accelerate-3.0.1.tar.gz'
    
    workdir = 'PyOpenGL-accelerate-3.0.1'
    
    def configure(self):
        pass
    
    def make(self):
        cmd = pythonExecutable+" setup.py build"
        self.system(cmd)
    def makeInstall(self):
        cmd = pythonExecutable+" setup.py install"
        self.system(cmd)
################################################################################################################

class PyOpenGLPackage(Package):
    src_uri = 'http://pypi.python.org/packages/source/P/PyOpenGL/PyOpenGL-3.0.1.tar.gz'
    
    workdir = 'PyOpenGL-3.0.1'
    
    def configure(self):
        pass
    
    def make(self):
        cmd = pythonExecutable+" setup.py build"
        self.system(cmd)
    def makeInstall(self):
        cmd = pythonExecutable+" setup.py install"
        self.system(cmd)

#####################################################################################################################

class Qimage2ndarrayPackage(Package):
    src_uri = 'http://kogs-www.informatik.uni-hamburg.de/~meine/software/qimage2ndarray/dist/qimage2ndarray-1.0.tar.gz'
    workdir = 'qimage2ndarray-1.0'

    if platform.system() == "Darwin":
        patches = ['qimage2array.patch']

    def unpack(self):
        Package.unpack(self)
        if platform.system() == "Darwin":
            self.system("sed -i '.bkp' -e 's|config.qt_inc_dir|\"%s\"|g' setup.py" % \
                        (self.prefix+"/include/"))
            self.system("sed -i '.bkp' -e 's|config.qt_lib_dir|\"%s\"|g' setup.py" % \
                        (self.prefix+"/lib"))

    def configure(self):
    	pass
    
    def make(self):
        self.system("%s setup.py build" % pythonExecutable)
    
    def makeInstall(self):
        self.system("%s setup.py install --prefix=%s" % (pythonExecutable, pythonVersionPath))

################################################################################################

class VTKGitPackage(Package):
    src_uri = "http://www.vtk.org/files/release/5.8/vtk-5.8.0.tar.gz"
    workdir = 'VTK' # kitware is wonderful
    
    def unpack(self):
        Package.unpack(self)
    
    def configure(self):
        cmd = cmake + """ . \\
        -DVTK_PYTHON_SETUP_ARGS=--prefix='%s'\\
        -DSIP_EXECUTABLE:FILEPATH=%s/sip\\
        -DSIP_INCLUDE_DIR:PATH=%s/sip\\
        -DSIP_PYQT_DIR:PATH=%s/sip/PyQt4\\
        -DVTK_WRAP_PYTHON_SIP:BOOL=ON\\
        -DPYTHON_EXECUTABLE:FILEPATH=%s\\
        -DPYTHON_INCLUDE_DIR:PATH=%s\\
        -DPYTHON_LIBRARY:FILEPATH=%s\\
        -DVTK_WRAP_PYTHON:BOOL=ON\\
        -DVTK_WRAP_PYTHON_SIP:BOOL=ON\\
        -DCMAKE_SHARED_LIBS:BOOL=ON\\
        -DVTK_USE_QT:BOOL=ON\\
        -DVTK_USE_QVTK_QTOPENGL:BOOL=ON\\
        -DVTK_USE_SYSTEM_HDF5:BOOL=ON\\
        -DCMAKE_INSTALL_PREFIX=%s \\
        -DVTK_INSTALL_LIB_DIR=lib \\
        -DVTK_INSTALL_INCLUDE_DIR=include \\
        -DVTK_INSTALL_PACKAGE_DIR=lib/vtk \\
        -DCMAKE_BUILD_TYPE=Release \\
        -DBUILD_EXAMPLES=OFF \\
        -DBUILD_TESTING=OFF \\
        -DVTK_USE_GEOVIS=ON \\
        -DVTK_USE_INFOVIS=ON \\
        -DVTK_USE_CHARTS=ON \\
        -DBUILD_SHARED_LIBS=ON \\
        -DVTK_USE_SYSTEM_EXPAT=ON \\
        -DVTK_USE_SYSTEM_FREETYPE=OFF \\
        -DVTK_USE_SYSTEM_JPEG=ON \\
        -DVTK_USE_SYSTEM_LIBXML2=OFF \\
        -DVTK_USE_SYSTEM_PNG=ON \\
        -DVTK_USE_SYSTEM_TIFF=ON \\
        -DVTK_USE_SYSTEM_ZLIB=ON \\
        -DVTK_USE_SYSTEM_HDF5=ON \\
        -DVTK_USE_HYBRID=ON \\
        -DVTK_USE_GL2PS=ON \\
        -DVTK_USE_RENDERING=ON \\
        -DVTK_WRAP_PYTHON=ON \\
        -DVTK_WRAP_PYTHON_SIP=ON \\
        -DVTK_USE_QT=ON \\
        -DVTK_USE_QVTK=ON \\
        -DVTK_USE_QVTK_QTOPENGL=ON \\
        -DVTK_USE_QTOPENGL=ON \\
        -DVTK_WRAP_CPP=ON \\
        -DVTK_WRAP_UI=ON \\
        -DVTK_USE_TK:BOOL=OFF \\
        -DDESIRED_QT_VERSION=4 \\
        """ % (pythonVersionPath, pythonBinaryPath, pythonIncludePath, pythonSharePath, \
        pythonExecutable, pythonIncludePath, pythonLibrary, \
        self.prefix)
        self.system(cmd)

    def makeInstall(self):
        cmd = "make install"
        if platform.system() != "Darwin":
            #FIXME: on 'make install', cmake complains about this missing file
            #why?
            self.system("touch Utilities/metaIOConfig.h")
            cmd = "LD_LIBRARY_PATH=%s make install" % (self.prefix + "/lib",)
        self.system(cmd)


#####################################################################################################################################

class LISPackage(Package):
    src_uri = 'http://www.ssisc.org/lis/dl/lis-1.2.53.tar.gz'
    correctMD5sum = '275597239e7c47ab5aadeee7b7e2c6ce'
    workdir = 'lis-1.2.53'
    
    def configure_darwin(self):
        return './configure --enable-omp --prefix=%s --enable-shared=yes' % (self.prefix)
        
    def configure_linux(self):
        return './configure --enable-omp --prefix=%s --enable-shared=yes' % (self.prefix)
        

###############################################################################################################

class SetuptoolsPackage(Package):
    src_uri = "http://pypi.python.org/packages/source/s/setuptools/setuptools-0.6c11.tar.gz"
    workdir = "setuptools-0.6c11"
    
    def configure(self):
        pass
    
    def make(self):
        self.system(pythonExecutable+" setup.py build")
    
    def makeInstall(self):
        self.system(pythonExecutable+" setup.py install")

###############################################################################################################

class EnthoughtBasePackage(Package):
    src_uri = "http://enthought.com/repo/ets/EnthoughtBase-3.1.0.tar.gz"
    workdir = "EnthoughtBase-3.1.0"
    correctMD5sum = '1d8f6365d20dfd5c4232334e80b0cfdf'
    patches = ['pyqt-correct-api-version.patch']
    
    def configure(self):
        pass
    
    def make(self):
        self.system(pythonExecutable+" setup.py build")
    
    def makeInstall(self):
        self.system(pythonExecutable+" setup.py install")

###############################################################################################################

class TraitsPackage(Package):
    src_uri = "http://www.enthought.com/repo/ETS/Traits-3.6.0.tar.gz"
    workdir = "Traits-3.6.0"
    correctMD5sum = 'f20092b1de7c470f61cc95ff4f2090e2'
    
    def configure(self):
        pass
    
    def make(self):
        self.system(pythonExecutable+" setup.py build")
    
    def makeInstall(self):
        self.system(pythonExecutable+" setup.py install")

###################################################################################################

class TraitsBackendQtPackage(Package):
    src_uri = "http://www.enthought.com/repo/ETS/TraitsBackendQt-3.6.0.tar.gz"
    workdir = "TraitsBackendQt-3.6.0"
    correctMD5sum = 'a655ae137af4d8590739618926e21893'
    patches = ['enthought-no-webkit.patch', 'enthought-no-svg.patch']
    
    def configure(self):
        pass
    
    def make(self):
        self.system(pythonExecutable+" setup.py build")
    
    def makeInstall(self):
        self.system(pythonExecutable+" setup.py install")

###################################################################################################

class TraitsGUIPackage(Package):
    src_uri = "http://www.enthought.com/repo/ETS/TraitsGUI-3.6.0.tar.gz"
    workdir = "TraitsGUI-3.6.0"
    #correctMD5sum = 'a655ae137af4d8590739618926e21893'
    
    def configure(self):
        pass
    
    def make(self):
        self.system(pythonExecutable+" setup.py build")
    
    def makeInstall(self):
        self.system(pythonExecutable+" setup.py install")

###################################################################################################

class Py2appPackage(Package):
    src_uri = "http://pypi.python.org/packages/source/p/py2app/py2app-0.6.1.tar.gz"
    workdir = "py2app-0.6.1"
    correctMD5sum = 'c60eee8f519c93070329de9adeeb14d6'
    
    def configure(self):
        pass
    
    def make(self):
        self.system(pythonExecutable+" setup.py build")
    
    def makeInstall(self):
        self.system(pythonExecutable+" setup.py install")
   
###################################################################################################

class CStraehlePackage(Package):
    src_uri = ''
    workdir = 'cstraehl-vigranumpy'
    if platform.system() == 'Darwin':
        patches = ['link-svs-darwin.patch']
    else:
        patches = ['link-svs-linux.patch']
    
    def __init__(self):
        if not os.path.exists("cstraehle-git-url.txt"):
            raise RuntimeError("You need to put the git:// url into a file called 'cstraehle-git-url.txt'")
        f = open("cstraehle-git-url.txt", 'r')
        l = f.readlines()[0]
        CStraehlePackage.src_uri = l.strip()
        Package.__init__(self)
    
    def configure(self):
        pass
    def make(self):
        pass
    def makeInstall(self):
        pass    

###################################################################################################


class PriowsPackage(Package):
    src_uri = 'git://github.com/cstraehl/priows.git'
    workdir = 'priows'
    
    def configure(self):
        self.system("git checkout 6e36582dec7d00809044ba551a298e844bb7676d")
        cmd = """%s . \\
        -DDEPENDENCY_SEARCH_PREFIX=%s \\
        -DCMAKE_INSTALL_PREFIX=%s \\
        -DBOOST_ROOT=%s \\
        -DCMAKE_BUILD_TYPE=Release \\
        -DPYTHON_EXECUTABLE=%s \\
        -DPYTHON_LIBRARY:FILEPATH=%s \\
        -DPYTHON_LIBRARIES:FILEPATH=%s \\
        -DPYTHON_INCLUDE_PATH:PATH=%s \\
        -DPYTHON_INCLUDE_DIR:PATH=%s \\
        -DPY_VIGRA=%s/vigra \\
        """ % (cmake, self.prefix, self.prefix, self.prefix, \
               pythonExecutable, pythonLibrary, pythonLibrary,
               pythonIncludePath, pythonIncludePath, pythonSitePackages)
        self.system(cmd)

    def make(self, parallel = multiprocessing.cpu_count()):
        self.system(make + " -j" + str(parallel))

###################################################################################################

class VigraPackage(Package):
    src_uri = 'git://github.com/Ilastik/vigra-ilastik-05.git'
    workdir = 'vigra'
    
    def configure(self):
        self.system("git checkout ilastik-0.5-base")
        dylibext = "dylib"
        if platform.system() != "Darwin":
            dylibext = "so"
        
        cmd = """%s . \\
        -DDEPENDENCY_SEARCH_PREFIX=%s \\
        -DCMAKE_INSTALL_PREFIX=%s \\
        -DBOOST_ROOT=%s \\
        -DWITH_VIGRANUMPY=1 \\
        -DCMAKE_BUILD_TYPE=Release \\
        -DPYTHON_EXECUTABLE=%s \\
        -DPYTHON_LIBRARY:FILEPATH=%s \\
        -DPYTHON_LIBRARIES:FILEPATH=%s \\
        -DPYTHON_INCLUDE_PATH:PATH=%s \\
        -DPYTHON_INCLUDE_DIR:PATH=%s \\
        -DLIS_INCLUDE_DIR=%s/include \\
        -DLIS_LIBRARY=%s/lib/liblis.%s\\
        """ % (cmake, self.prefix, self.prefix, self.prefix, \
               pythonExecutable, pythonLibrary, pythonLibrary, pythonIncludePath, pythonIncludePath, \
               self.prefix, self.prefix, dylibext,)
        self.system(cmd)
        
        os.system('cd work/vigra && patch --forward -p0 < ../../files/vigra_include_private.patch')
        #############self.system('cd vigranumpy && cp -r ../../cstraehl-vigranumpy private')
        
        #reconfigure now that we have added the private dir!
        self.system(cmd)
        
    def make(self, parallel = multiprocessing.cpu_count()):
        self.system(make + " -j" + str(parallel))
