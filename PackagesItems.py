#!/usr/bin/env python
# -*- coding: utf-8 -*-

import __builtin__
from PackagesBase import Package
import os, platform
import urllib2, os, tarfile, shutil
import multiprocessing
        



#===============================================================================
# CmakePackage
#===============================================================================
class CmakePackage(Package):
    src_uri = 'http://www.cmake.org/files/v2.8/cmake-2.8.7.tar.gz'
    
    def configure_darwin(self):
        return ['./configure', '--prefix="($prefix)"']
        
#===============================================================================
# GitPackage
#===============================================================================
class GitPackage(Package):
    src_uri = 'http://git-core.googlecode.com/files/git-1.7.9.6.tar.gz'
    
    def configure_darwin(self):
        return ['./configure', '--bindir="($prefix)/bin"', '--libdir="($prefix)/lib"', 
                '--includedir="($prefix)/include"', '--prefix="($prefix)"']
#===============================================================================
# ZlibPackage
#===============================================================================
class ZlibPackage(Package):
    src_uri = 'http://sourceforge.net/projects/libpng/files/zlib/1.2.6/zlib-1.2.6.tar.gz'
    
    def configure_darwin(self):
        return ['./configure', '--64', '--prefix="($prefix)"', '--libdir="($prefix)/lib"', 
        		'--sharedlibdir="($prefix)/lib"', '--includedir="($prefix)/include"']

#===============================================================================
# SlibPackage
#===============================================================================
class SlibPackage(Package):
    src_uri='http://www.hdfgroup.org/ftp/lib-external/szip/2.1/src/szip-2.1.tar.gz'
    
    def configure_darwin(self):
        return ['./configure', '--bindir="($prefix)/bin"', '--libdir="($prefix)/lib"', 
                '--includedir="($prefix)/include"', '--enable-static=no', '--prefix="($prefix)"']
    
#===============================================================================
# PythonPackage
#===============================================================================
class PythonPackage(Package):
    src_uri='http://www.python.org/ftp/python/2.7.3/Python-2.7.3.tgz'

    def configure_darwin(self):
        return ['./configure', '--prefix="($prefix)"', '--enable-framework="($prefix)/Frameworks"']

#===============================================================================
# FFTW3Package
#===============================================================================
class FFTW3Package(Package):
    src_uri='http://www.fftw.org/fftw-3.3.1.tar.gz'
    
    def configure_darwin(self):
        return ['./configure', '--prefix="($prefix)"', '--bindir="($prefix)/bin"', 
                '--libdir="($prefix)/lib"', '--includedir="($prefix)/include"', 
                '--enable-shared=yes', '--enable-static=no', '--disable-fortran']

#===============================================================================
# FFTW3FPackage
#===============================================================================
class FFTW3FPackage(Package):
    src_uri='http://www.fftw.org/fftw-3.3.1.tar.gz'
    
    def configure_darwin(self):
        return ['./configure', '--prefix="($prefix)"', '--bindir="($prefix)/bin"', 
                '--libdir="($prefix)/lib"', '--includedir="($prefix)/include"', 
                '--enable-shared=yes', '--enable-static=no', '--disable-fortran', '--enable-single']
    
#===============================================================================
# JpegPackage
#===============================================================================
class JpegPackage(Package):
    src_uri='http://www.ijg.org/files/jpegsrc.v8d.tar.gz'
    
    def configure_darwin(self):
        return ['./configure', '--prefix="($prefix)"', '--bindir="($prefix)/bin"', 
                '--libdir="($prefix)/lib"', '--enable-shared=yes', '--enable-static=no']
    
#===============================================================================
# TiffPackage
#===============================================================================
class TiffPackage(Package):
    src_uri='ftp://ftp.remotesensing.org/pub/libtiff/tiff-3.9.6.tar.gz'
    
    def configure_darwin(self):
        return ['./configure', '--prefix="($prefix)"', '--bindir="($prefix)/bin"', 
                '--libdir="($prefix)/lib"', '--includedir="($prefix)/include"', '--enable-shared=yes', 
                '--enable-static=no', '--with-zlib-include-dir="($prefix)/include"', 
                '--with-zlib-lib-dir="($prefix)/lib"', '--with-jpeg-include-dir="($prefix)/include"', 
                '--with-jpeg-lib-dir="($prefix)/lib"', '--with-apple-opengl-framework']
    
#===============================================================================
# PngPackage
#===============================================================================
class PngPackage(Package):
    src_uri='http://prdownloads.sourceforge.net/libpng/libpng-1.5.10.tar.gz'
    
    def configure_darwin(self):
        return ['./configure', '--prefix="($prefix)"', '--bindir="($prefix)/bin"', '--libdir="($prefix)/lib"', 
                '--includedir="($prefix)/include"', '--enable-shared=yes', '--enable-static=no']    
    
#===============================================================================
# SetuptoolsPackage
#===============================================================================
class SetuptoolsPackage(Package):
    src_uri='http://pypi.python.org/packages/source/s/setuptools/setuptools-0.6c11.tar.gz'
    
    def configure(self):
        pass
    
    def make(self):
        self.system("python setup.py build")
    
    def makeInstall(self):
        self.system("python setup.py install")
    
#===============================================================================
# NosePackage
#===============================================================================
class NosePackage(Package):
    src_uri='http://pypi.python.org/packages/source/n/nose/nose-1.1.2.tar.gz'
    
    def configure(self):
        pass
    
    def make(self):
        self.system("python setup.py build")
    
    def makeInstall(self):
        self.system("python setup.py install")
    
#===============================================================================
# Hdf5Package
#===============================================================================
class Hdf5Package(Package):
    src_uri='http://www.hdfgroup.org/ftp/HDF5/current/src/hdf5-1.8.8.tar.gz'
    
    def configure_darwin(self):
        return ['./configure', 
                '--prefix="($prefix)"', 
                '--bindir="($prefix)/bin"', 
                '--libdir="($prefix)/lib"', 
                '--includedir="($prefix)/include"', 
                '--enable-shared=yes', 
                '--enable-static=no', 
                '--with-zlib="($prefix)"']

#===============================================================================
# NumpyPackage
#===============================================================================
class NumpyPackage(Package):
    src_uri='http://downloads.sourceforge.net/project/numpy/NumPy/1.6.1/numpy-1.6.1.tar.gz'
    
    def configure(self):
        pass
    
    def make(self):
        self.system("python setup.py build")
    
    def makeInstall(self):
        self.system("python setup.py install")   
    
#===============================================================================
# H5pyPackage
#===============================================================================
class H5pyPackage(Package):
    src_uri='http://h5py.googlecode.com/files/h5py-2.0.1.tar.gz'
    
    def configure_darwin(self):
        return ['python', 'setup.py', 'build', '--hdf5="($prefix)"']
    
    def make(self):
        pass
    
    def makeInstall(self):
        self.system("python setup.py install")
    
#===============================================================================
# BoostPackage
#===============================================================================
class BoostPackage(Package):
    src_uri='http://sourceforge.net/projects/boost/files/boost/1.49.0/boost_1_49_0.tar.gz'
    
    def configure_darwin(self):
        return ['./bootstrap.sh', '--prefix="($prefix)"', '--libdir=="($prefix)/lib"', '--with-python="($prefix)/bin/python"', 
                '--with-libraries=python',
                '&&',
                './bjam', 'install', '--prefix="($prefix)"', 'address-model=64', 
                #'macosx-version-min=10.6'
                ]
    
    def make(self):
        pass
    
    def makeInstall(self):
        pass
    
#===============================================================================
# VigraPackage
#===============================================================================
class VigraPackage(Package):
    src_uri = 'git://github.com/ukoethe/vigra.git'
    
    def configure_darwin(self):
        return ['cmake . ',
                '-DDEPENDENCY_SEARCH_PREFIX=($prefix)', 
                '-DCMAKE_INSTALL_PREFIX=($prefix)', 
                '-DBOOST_ROOT=($prefix)', 
                '-DWITH_VIGRANUMPY=1', 
                '-DCMAKE_BUILD_TYPE=Release', 
                '-DPYTHON_INCLUDE_DIR=($pythonHeaders)',
                '-DPYTHON_LIBRARY=($pythonlib)',
                ]
    
#===============================================================================
# QtPackage
#===============================================================================
class QtPackage(Package):
    src_uri='http://download.qt.nokia.com/qt/source/qt-everywhere-opensource-src-4.8.1.tar.gz'
    
    def configure_darwin(self):
        return ['echo', "'yes'", '| ./configure', 
                '-no-framework', 
                '--prefix="($prefix)"', 
                '-opensource', 
                '-arch x86_64', 
                '-optimized-qmake', 
                '-nomake examples', 
                '-nomake demos', 
                '-nomake docs', 
                '-nomake translations', 
                '-no-multimedia', 
                '-no-svg', 
                '-no-audio-backend', 
                '-no-phonon', 
                '-no-phonon-backend', 
                '-no-svg', 
                '-no-sql-sqlite', 
                '-no-sql-sqlite2', 
                '-no-sql-psql', 
                '-no-sql-db2', 
                '-no-sql-ibase', 
                '-no-sql-mysql', 
                '-no-sql-oci', 
                '-no-sql-odbc', 
                '-no-sql-sqlite_symbian', 
                '-no-sql-tds', 
                '-no-pch', 
                '-no-dbus', 
                '-no-cups', 
                '-no-nis', 
                '-qt-libpng', 
                '-release', 
                '-shared', 
                '-no-accessibility', 
                '-L/usr/X11/lib', 
                '-I/usr/X11/include', 
                '-cocoa',
                ]
    
#===============================================================================
# SipPackage
#===============================================================================
class SipPackage(Package):
    src_uri='http://www.riverbankcomputing.co.uk/static/Downloads/sip4/sip-4.13.2.tar.gz'
    
    def configure_darwin(self):
        return ['python', 'configure.py', '--arch=x86_64']
    
#===============================================================================
# PyQtPackage
#===============================================================================
class PyQtPackage(Package):
    src_uri='http://www.riverbankcomputing.co.uk/static/Downloads/PyQt4/PyQt-mac-gpl-4.9.1.tar.gz'
    
    def configure_darwin(self):
        return ['python', 'configure.py', '--confirm-license', '-q', '"($prefix)/bin/qmake"', '--use-arch=x86_64']

#===============================================================================
# Qimage2ndarrayPackage
#===============================================================================
class Qimage2ndarrayPackage(Package):
    src_uri='http://kogs-www.informatik.uni-hamburg.de/~meine/software/qimage2ndarray/dist/qimage2ndarray-1.0.tar.gz'
    replaceLines = ['setup.py', ('qt_inc_dir = config.qt_inc_dir', 'qt_inc_dir ="' + installDir + '/include"\n'), ('qt_lib_dir=config.qt_lib_dir','qt_lib_dir="' + installDir + '/lib"'),
                    ("# Qt is distributed as 'framework' on OS X; obviously we need this","    pass\n"),
                    ('for lib in qt_libraries:','#\n'),
                    ("qimageview.extra_link_args.extend(['-framework', lib])",'#\n'),
                    ('for d in qt_lib_dirs:','#\n'),
                    ("qimageview.extra_link_args.append('-F' + d)",'#\n'),] 
    
    def configure_darwin(self):
        return ['python', 'setup.py', 'build',
                '&&',
                'python', 'setup.py', 'install', '--prefix="($prefix)/Frameworks/Python.framework/Versions/2.7"',
                ]
    
    def make(self):
        pass
    
    def makeInstall(self):
        pass
    
#===============================================================================
# GreenletPackage
#===============================================================================
class GreenletPackage(Package):
    src_uri='git://github.com/python-greenlet/greenlet.git'
    
    def configure(self):
        pass
    
    def make(self):
        self.system("python setup.py build")
    
    def makeInstall(self):
        self.system("python setup.py install") 
        
#===============================================================================
# BlistPackage
#===============================================================================
class BlistPackage(Package):
    src_uri='http://pypi.python.org/packages/source/b/blist/blist-1.3.4.tar.gz'
    
    def configure(self):
        pass
    
    def make(self):
        self.system("python setup.py build")
    
    def makeInstall(self):
        self.system("python setup.py install") 
        
#===============================================================================
# PsutilPackage
#===============================================================================
class PsutilPackage(Package):
    src_uri='http://psutil.googlecode.com/files/psutil-0.4.1.tar.gz'
    
    def configure(self):
        pass
    
    def make(self):
        self.system("python setup.py build")
    
    def makeInstall(self):
        self.system("python setup.py install") 

#===============================================================================
# IpythonPackage
#===============================================================================
class IpythonPackage(Package):
    src_uri='http://archive.ipython.org/release/0.12/ipython-0.12.tar.gz'
    
    def configure(self):
        pass
    
    def make(self):
        self.system("python setup.py build")
    
    def makeInstall(self):
        self.system("python setup.py install") 
    
#===============================================================================
# ReadlinePackage
#===============================================================================
class ReadlinePackage(Package):
    src_uri='http://pypi.python.org/packages/source/r/readline/readline-6.2.2.tar.gz'
    
    def configure(self):
        pass
    
    def make(self):
        self.system("python setup.py build")
    
    def makeInstall(self):
        self.system("python setup.py install") 
    
#===============================================================================
# VTKPackage
#===============================================================================
class VTKPackage(Package):
    src_uri='http://www.vtk.org/files/release/5.10/vtk-5.10.0-rc1.tar.gz'
    replaceLines = ['Wrapping/Python/CMakeLists.txt', ('SET(VTK_PYTHON_SETUP_ARGS','      SET(VTK_PYTHON_SETUP_ARGS --prefix=' + installDir + '/Frameworks/Python.framework/Versions/2.7 \n')]
    
    def configure_darwin(self):
        return ['cmake . ',
                '-DSIP_EXECUTABLE:FILEPATH=($pythonBinaryPath)/sip',
                '-DSIP_INCLUDE_DIR:PATH=($pythonIncludePath)/sip',
                '-DSIP_PYQT_DIR:PATH=($pythonSharePath)/sip/PyQt4',
                '-DVTK_WRAP_PYTHON_SIP:BOOL=ON',
                '-DPYTHON_EXECUTABLE:FILEPATH=($pythonExecutable)',
                '-DPYTHON_INCLUDE_DIR:PATH=($pythonIncludePath)',
                '-DPYTHON_LIBRARY:FILEPATH=($pythonlib)',
                '-DVTK_WRAP_PYTHON:BOOL=ON',
                '-DVTK_WRAP_PYTHON_SIP:BOOL=ON',
                '-DCMAKE_SHARED_LIBS:BOOL=ON',
                '-DVTK_USE_QT:BOOL=ON',
                '-DVTK_USE_QVTK_QTOPENGL:BOOL=ON',
                '-DVTK_USE_SYSTEM_HDF5:BOOL=ON',
                '-DCMAKE_INSTALL_PREFIX=%s',
                '-DVTK_INSTALL_LIB_DIR=lib',
                '-DVTK_INSTALL_INCLUDE_DIR=include',
                '-DVTK_INSTALL_PACKAGE_DIR=lib/vtk',
                '-DCMAKE_BUILD_TYPE=Release',
                '-DBUILD_EXAMPLES=OFF',
                '-DBUILD_TESTING=OFF',
                '-DVTK_USE_GEOVIS=ON',
                '-DVTK_USE_INFOVIS=ON',
                '-DVTK_USE_CHARTS=ON',
                '-DBUILD_SHARED_LIBS=ON',
                '-DVTK_USE_SYSTEM_EXPAT=ON',
                '-DVTK_USE_SYSTEM_FREETYPE=OFF',
                '-DVTK_USE_SYSTEM_JPEG=ON',
                '-DVTK_USE_SYSTEM_LIBXML2=OFF',
                '-DVTK_USE_SYSTEM_PNG=ON',
                '-DVTK_USE_SYSTEM_TIFF=ON',
                '-DVTK_USE_SYSTEM_ZLIB=ON',
                '-DVTK_USE_SYSTEM_HDF5=ON',
                '-DVTK_USE_HYBRID=ON',
                '-DVTK_USE_GL2PS=ON',
                '-DVTK_USE_RENDERING=ON',
                '-DVTK_WRAP_PYTHON=ON',
                '-DVTK_WRAP_PYTHON_SIP=ON',
                '-DVTK_USE_QT=ON',
                '-DVTK_USE_QVTK=ON',
                '-DVTK_USE_QVTK_QTOPENGL=ON',
                '-DVTK_USE_QTOPENGL=ON',
                '-DVTK_WRAP_CPP=ON',
                '-DVTK_WRAP_UI=ON',
                '-DVTK_USE_TK:BOOL=OFF',
                '-DDESIRED_QT_VERSION=4',
                '-DJPEG_INCLUDE_DIR=($prefix)/include',
                '-DJPEG_LIBRARY=($prefix)/lib/libjpeg.dylib',
                '-DPNG_LIBRARY=($prefix)/lib/libpng.dylib',
                '-DPNG_PNG_INCLUDE_DIR=($prefix)/include',
                '-DTIFF_INCLUDE_DIR=($prefix)/include',
                '-DTIFF_LIBRARY=($prefix)/lib/libtiff.dylib',
                '-DZLIB_INCLUDE_DIR=($prefix)/include',
                '-DZLIB_LIBRARY=($prefix)/lib/libz.dylib', 
                '-DHDF5_HL_INCLUDE_DIR=($prefix)/include',
                '-DCMAKE_INSTALL_PREFIX=($prefix)',
                '../../work/($packageWorkDir)']

#===============================================================================
# LazyflowPackage
#===============================================================================
class LazyflowPackage(Package):
    src_uri = 'git://github.com/Ilastik/lazyflow.git'
    
    def configure_darwin(self):
        return ['cd .. && cp -r %s ($prefix)/%s' % (self.workdir, self.workdir),
        		' && cd ($prefix)/%s/lazyflow/drtile' % (self.workdir), ' && pwd',
        		' && cmake .',
        		'-DBoost_INCLUDE_DIR=($prefix)/include',
        		'-DBoost_PYTHON_LIBRARY_DEBUG=($prefix)/lib/libboost_python.dylib',
        		'-DBoost_PYTHON_LIBRARY_RELEASE=($prefix)/lib/libboost_python.dylib',
        		'-DPYTHON_INCLUDE_DIR=($pythonHeadersPath)',
        		'-DPYTHON_LIBRARY=($pythonlib)',
        		'-DVIGRA_IMPEX_LIBRARY=($prefix)/lib/libvigraimpex.dylib',
        		'-DVIGRA_IMPEX_LIBRARY_DIR=($prefix)/lib',
        		'-DVIGRA_INCLUDE_DIR=($prefix)/include',
        		' && make',
        		]
    
    def make(self):
        pass
    def makeInstall(self):
        pass
    
#===============================================================================
# VoluminaPackage
#===============================================================================
class VoluminaPackage(Package):
    src_uri = 'git://github.com/Ilastik/volumina.git'
    
    def configure_darwin(self):
        return ['cd .. && cp -r %s ($prefix)/%s' % (self.workdir, self.workdir),
				]
            
    def make(self):
        pass
    def makeInstall(self):
        pass

#===============================================================================
# WidgetsPackage
#===============================================================================
class WidgetsPackage(Package):
    src_uri = 'git://github.com/Ilastik/widgets.git'
    
    def configure_darwin(self):
        return ['cd .. && cp -r %s ($prefix)/%s' % (self.workdir, self.workdir),
				]
            
    def make(self):
        pass
    def makeInstall(self):
        pass

#===============================================================================
# TechpreviewPackage
#===============================================================================
class TechpreviewPackage(Package):
    src_uri = 'git://github.com/Ilastik/techpreview.git'
    
    def configure_darwin(self):
        return ['cd .. && cp -r %s ($prefix)/%s' % (self.workdir, self.workdir),
				]
            
    def make(self):
        pass
    def makeInstall(self):
        pass
    
#===============================================================================
# EnvironmentScript
#===============================================================================
class EnvironmentScript(object):
    def __init__(self):
        self.createFile()
    
    def createFile(self):
        file = open('%s/activate.sh' % (installDir), "w")
        file.write("export PATH=%s/bin:%s/Frameworks/Python.framework/Versions/2.7/bin:$PATH\n" % (installDir, installDir))
        file.write("export DYLD_FALLBACK_LIBRARY_PATH=%s/lib:%s/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/vigra\n" % (installDir, installDir))
        file.write("export PYTHONPATH=%s/volumina:%s/widgets:%s/lazyflow:%s/lazyflow/lazyflow/drtile:%s/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages\n" % (installDir, installDir, installDir, installDir, installDir))
        file.write("alias classificationWorkflow='python %s/techpreview/classification/classificationWorkflow.py'\n" % (installDir))
        file.write("txtred='\e[0;31m' # Red\n")
        file.write("bldgrn='\e[1;32m' # Green\n")
        file.write("txtrst='\e[0m'    # Text Reset\n")
        file.write("print_before_the_prompt () {\n")
        file.write('    printf "\n $txtred%s: $bldgrn%s \n$txtrst" "ilastik environment" "$PWD"\n')
        file.write("}\n")
        file.write("PROMPT_COMMAND=print_before_the_prompt\n")
        file.write("PS1='-> '")
        file.close()

#===============================================================================
# EnthoughtBasePackage
#===============================================================================
class EnthoughtBasePackage(Package):
    src_uri='http://enthought.com/repo/ets/EnthoughtBase-3.1.0.tar.gz'
    
    def configure(self):
        pass
    
    def make(self):
        self.system("python setup.py build")
    
    def makeInstall(self):
        self.system("python setup.py install") 
        
#===============================================================================
# TraitsPackage
#===============================================================================
class TraitsPackage(Package):
    src_uri='http://enthought.com/repo/ets/traits-4.0.0.tar.gz'
    
    def configure(self):
        pass
    
    def make(self):
        self.system("python setup.py build")
    
    def makeInstall(self):
        self.system("python setup.py install")
        
#===============================================================================
# TraitsBackendQtPackage
#===============================================================================
class TraitsBackendQtPackage(Package):
    src_uri='http://enthought.com/repo/ets/TraitsBackendQt-3.6.0.tar.gz'
    
    def configure(self):
        pass
    
    def make(self):
        self.system("python setup.py build")
    
    def makeInstall(self):
        self.system("python setup.py install")
        
#===============================================================================
# TraitsGUIPackage
#===============================================================================
class TraitsGUIPackage(Package):
    src_uri='http://enthought.com/repo/ets/TraitsGUI-3.6.0.tar.gz'
    
    def configure(self):
        pass
    
    def make(self):
        self.system("python setup.py build")
    
    def makeInstall(self):
        self.system("python setup.py install")    
    
#===============================================================================
# Vigra05Package
#===============================================================================
class Vigra05Package(Package):
    src_uri = 'git://github.com/Ilastik/vigra-ilastik-05.git'
    
    def configure_darwin(self):
        return ['cmake . ',
                '-DDEPENDENCY_SEARCH_PREFIX=($prefix)', 
                '-DCMAKE_INSTALL_PREFIX=($prefix)/vigra-ilastik-05', 
                '-DBOOST_ROOT=($prefix)', 
                '-DWITH_VIGRANUMPY=1', 
                '-DCMAKE_BUILD_TYPE=Release', 
                '-DPYTHON_INCLUDE_DIR=($pythonHeaders)',
                '-DPYTHON_LIBRARY=($pythonlib)',
                '-DPNG_LIBRARY=($prefix)/lib/libpng.dylib',
                '-DPNG_PNG_INCLUDE_DIR=($prefix)/include',
                ]
    
#===============================================================================
# IlastikPackage
#===============================================================================
class IlastikPackage(Package):
    src_uri = 'git://github.com/Ilastik/ilastik.git'
    
    def configure_darwin(self):
        return ['cd .. && cp -r %s ($prefix)/%s' % (self.workdir, self.workdir),
                '&& cd ($prefix)/%s' % (self.workdir),
                '&& git checkout rc-final',
                ]
            
    def make(self):
        pass
    def makeInstall(self):
        pass
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    