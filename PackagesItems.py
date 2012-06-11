#!/usr/bin/env python
# -*- coding: utf-8 -*-

import __builtin__
from PackagesBase import Package
import os, platform
import urllib2, os, tarfile, shutil
import multiprocessing, stat

#===============================================================================
# CmakePackage
#===============================================================================
class CmakePackage(Package):
    src_file = 'cmake.tar.gz'

    def configure_all(self):
        return ['./configure',
                '--prefix="($prefix)"']

#===============================================================================
# GitPackage
#===============================================================================
class GitPackage(Package):
    src_file = 'git.tar.gz'

    def configure_all(self):
        return ['./configure', '--bindir="($prefix)/bin"',
                '--libdir="($prefix)/lib"',
                '--includedir="($prefix)/include"',
                '--prefix="($prefix)"']
#===============================================================================
# ZlibPackage
#===============================================================================
class ZlibPackage(Package):
    src_file = 'zlib.tar.gz'

    def configure_all(self):
        return ['./configure',
                '--64',
                '--prefix="($prefix)"',
                '--libdir="($prefix)/lib"',
                '--sharedlibdir="($prefix)/lib"',
                '--includedir="($prefix)/include"'
               ]

#===============================================================================
# SlibPackage
#===============================================================================
class SlibPackage(Package):
    src_file = 'szip.tar.gz'

    def configure_all(self):
        return ['./configure',
                '--bindir="($prefix)/bin"',
                '--libdir="($prefix)/lib"',
                '--includedir="($prefix)/include"',
                '--enable-static=no',
                '--prefix="($prefix)"'
               ]

    def configure_darwin(self):
        return [
                #'--disable-dependency-tracking'
               ]

#===============================================================================
# PythonPackage
#===============================================================================
class PythonPackage(Package):
    src_file = 'python.tar.gz'

    def configure_all(self):
        return ['./configure',
                '--prefix="($prefix)"'
               ]

    def configure_linux(self):
        return [' --enable-shared']

    def configure_darwin(self):
        return ['--enable-framework="($prefix)/Frameworks"']

#===============================================================================
# FFTW3Package
#===============================================================================
class FFTW3Package(Package):
    src_file = 'fftw.tar.gz'

    def configure_all(self):
        return ['./configure',
                '--enable-portable-binary',
                '--prefix="($prefix)"',
                '--bindir="($prefix)/bin"',
                '--libdir="($prefix)/lib"',
                '--includedir="($prefix)/include"',
                '--enable-shared=yes',
                '--disable-fortran'
               ]

    def configure_darwin(self):
        return ['--enable-static=no'
                #, '--disable-dependency-tracking'
               ]

#===============================================================================
# FFTW3FPackage
#===============================================================================
class FFTW3FPackage(Package):
    src_file = 'fftw.tar.gz'

    def configure_all(self):
        return ['./configure',
                '--enable-single',
                '--enable-portable-binary',
                '--prefix="($prefix)"',
                '--bindir="($prefix)/bin"',
                '--libdir="($prefix)/lib"',
                '--includedir="($prefix)/include"',
                '--enable-shared=yes',
                '--disable-fortran'
               ]

    def configure_darwin(self):
        return ['--enable-static=no'
                #, '--disable-dependency-tracking'
               ]

#===============================================================================
# JpegPackage
#===============================================================================
class JpegPackage(Package):
    src_file = 'jpegsrc.tar.gz'

    def configure_all(self):
        return ['./configure',
                '--prefix="($prefix)"',
                '--bindir="($prefix)/bin"',
                '--libdir="($prefix)/lib"',
                '--enable-shared=yes'
               ]

    def configure_darwin(self):
        return ['--enable-static=no'
                #, '--disable-dependency-tracking'
               ]

#===============================================================================
# TiffPackage
#===============================================================================
class TiffPackage(Package):
    src_file = 'tiff.tar.gz'

    def configure_all(self):
        return ['./configure',
                '--prefix="($prefix)"',
                '--bindir="($prefix)/bin"',
                '--libdir="($prefix)/lib"',
                '--includedir="($prefix)/include"',
                '--enable-shared=yes',
                '--with-zlib-include-dir="($prefix)/include"',
                '--with-zlib-lib-dir="($prefix)/lib"',
                '--with-jpeg-include-dir="($prefix)/include"',
                '--with-jpeg-lib-dir="($prefix)/lib"'
               ]

    def configure_darwin(self):
        return ['--enable-static=no',
                '--with-apple-opengl-framework']

#===============================================================================
# PngPackage
#===============================================================================
class PngPackage(Package):
    src_file = 'libpng.tar.gz'

    def configure_all(self):
        return ['./configure',
                '--prefix="($prefix)"',
                '--bindir="($prefix)/bin"',
                '--libdir="($prefix)/lib"',
                '--includedir="($prefix)/include"',
                '--enable-shared=yes',
                '--enable-static=no']

#===============================================================================
# SetuptoolsPackage
#===============================================================================
class SetuptoolsPackage(Package):
    src_file = 'setuptools.tar.gz'

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
    src_file = 'nose.tar.gz'

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
    src_file = 'hdf5.tar.gz'

    def configure_all(self):
        return ['./configure',
                '--prefix="($prefix)"',
                '--bindir="($prefix)/bin"',
                '--libdir="($prefix)/lib"',
                '--includedir="($prefix)/include"',
                '--enable-shared=yes',
                '--enable-static=no',
                '--with-zlib="($prefix)"']

    def configure_darwin(self):
        return [
                # '--disable-dependency-tracking'
               ]


#===============================================================================
# NumpyPackage
#===============================================================================
class NumpyPackage(Package):
    src_file = 'numpy.tar.gz'

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
    src_file = 'h5py.tar.gz'

    def configure_all(self):
        return ['python', 'setup.py', 'build', '--hdf5="($prefix)"']

    def make(self):
        pass

    def makeInstall(self):
        self.system("python setup.py install")

#===============================================================================
# BoostPackage
#===============================================================================
class BoostPackage(Package):
    src_file = 'boost.tar.gz'

    def configure_all(self):
        return ['./bootstrap.sh',
                '--prefix="($prefix)"',
                '--libdir=="($prefix)/lib"',
                '--with-python="($prefix)/bin/python"',
                '--with-libraries=python',
                '&&',
                './bjam',
                'install',
                '--prefix="($prefix)"',
               ]

    def configure_darwin(self):
        return ['address-model=64'
                #, 'macosx-version-min=10.6'
               ]

    def make(self):
        pass

    def makeInstall(self):
        pass

#===============================================================================
# VigraPackage
#===============================================================================
class VigraPackage(Package):
    src_file = 'vigra.tar'

    def configure_all(self):
        return ['cmake . ',
                '-DDEPENDENCY_SEARCH_PREFIX=($prefix)',
                '-DCMAKE_INSTALL_PREFIX=($prefix)',
                '-DBOOST_ROOT=($prefix)',
                '-DWITH_VIGRANUMPY=1',
                '-DCMAKE_BUILD_TYPE=Release',
                '-DPYTHON_INCLUDE_DIR=($pythonHeadersPath)',
                '-DPYTHON_LIBRARY=($pythonlib)',
               ]

    def configure_linux(self):
        return [
                '-DPYTHON_EXECUTABLE=($pythonExecutable)',
                '-DPYTHON_LIBRARIES:FILEPATH=($pythonlib)', #new PYTHON_LIBRARY?
                '-DPYTHON_INCLUDE_PATH:PATH=($pythonIncludePath)'
               ]

   # configure_darwin probably missing.

   ##     -DLIS_INCLUDE_DIR=%s/include \\
   ##     -DLIS_LIBRARY=%s/lib/liblis.%s\\
   ###     """ % (......, dylibext)

#===============================================================================
# QtPackage
#===============================================================================
class QtPackage(Package):
    src_file = 'qt.tar.gz'

    def configure_all(self):
        return ['echo', "'yes'", '| ./configure',
                '--prefix="($prefix)"',
                '-opensource',
                '-arch x86_64',
                '-optimized-qmake',
                '-nomake examples',
                '-nomake demos',
                '-nomake docs',
                '-nomake translations',
                ####'-nomake tools',  #$#
                '-no-multimedia',
                '-no-xmlpatterns',####  #$#
                '-no-svg',
                '-no-audio-backend',
                '-no-phonon',
                '-no-phonon-backend',
                '-no-webkit', #$#
                '-no-openssl', #$# # inconclusive for pyqt491 problems
                '-no-declarative', #$#
                '-no-declarative-debug', #$#
                '-no-script', #$#
                '-no-scripttools', #$#
                '-no-javascript-jit', #$#
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
                #'-no-qt3support',
                '-no-3dnow',
                #'-no-sse2', for 32 bit builds only
                '-no-ssse3',
                '-no-sse4.1',
                '-no-sse4.2',
                '-no-avx',
                '-release',
                #$# '-fast',
                '-shared',
                '-no-accessibility',
                #__#'-L/usr/X11/lib',      ### for Darwin?
                #__#'-I/usr/X11/include',  ### for Darwin?
               ]

    def configure_rc(self):
        return ['echo', "'yes'", '| ./configure',
                #'-opensource',
                #'-arch x86_64',
                #'-optimized-qmake',
                #'-nomake examples',
                #'-nomake demos',
                #'-nomake docs',
                #'-nomake translations',
                #_#'-nomake tools',
                #'-no-multimedia',
                #_#'-no-xmlpatterns',
                #'-no-svg',
                #'-no-audio-backend',
                #'-no-phonon',
                #'-no-phonon-backend',
                #$#'-no-webkit',
                #$#'-no-openssl',
                #$#'-no-declarative',
                #$#'-no-declarative-debug',
                #$#'-no-script',
                #$#'-no-scripttools',
                #$#'-no-javascript-jit',
                #'-no-sql-sqlite',
                #'-no-sql-sqlite2',
                #'-no-sql-psql',
                #'-no-sql-db2',
                #'-no-sql-ibase',
                #'-no-sql-mysql',
                #'-no-sql-oci',
                #'-no-sql-odbc',
                #'-no-sql-sqlite_symbian',
                #'-no-sql-tds',
                #'-no-pch',
                #'-no-dbus',
                #'-no-cups',
                #'-no-nis',
                #'-qt-libpng',
                '-fast',
                #'-release',
                #'-shared',
                #'-no-accessibility'
               ]


    def configure_linux(self):
        return ['-no-script -no-scripttools -no-javascript-jit',
                '-fast',
                '-no-sse3',
                ' --enable-shared'
               ]

    def configure_darwin(self):
        return ['-no-framework',
                '-cocoa'
                ####, '-no-dwarf2'
               ]
        
    def configure_windows(self):
        return [
                '-no-sse3'
               ]

    def old_make(self, parallel = multiprocessing.cpu_count()):
        self.system(make + " -j" + str(parallel))
        
        #Also install Designer, which is needed by VTK
        self.system(("cd tools/designer && ../../bin/qmake && %s "
                     + " && %s install")
                    % (make, make))
        
    def fixOrTest(self):
        pass
#        os.system('cp -rv work/%s/src/gui/mac/qt_menu.nib %s/lib'
#                   % (self.workdir, installDir))
#        #^Mac...

#===============================================================================
# SipPackage
#===============================================================================
class SipPackage(Package):
    src_file = 'sip.tar.gz'

    def configure_all(self):
        return ['python', 'configure.py']

    def configure_darwin(self):
        return ['--arch=x86_64']
    
    #def configure_linux(self):
    #   ###self.prefix + "/include/sip"


#===============================================================================
# PyQtPackage
#===============================================================================
class PyQtPackage(Package):
    src_file = 'pyqt.tar.gz'

     # "%s" % (pythonExecutable)

    def configure_all(self):
        return ['python',
                'configure.py',
                '--confirm-license',
                '-q',
                '"($prefix)/bin/qmake"'
               ]

##    def configure_linux(self):
##        return ['--no-designer-plugin']

    def configure_darwin(self):
        return ['--use-arch=x86_64']


#===============================================================================
# Qimage2ndarrayPackage
#===============================================================================
class Qimage2ndarrayPackage(Package):
    src_file = 'qimage2ndarray.tar.gz'

    replaceDarwin = ['setup.py',
                     ('qt_inc_dir = config.qt_inc_dir',
                      'qt_inc_dir ="' + installDir + '/include"\n'),
                     ('qt_lib_dir=config.qt_lib_dir',
                      'qt_lib_dir="' + installDir + '/lib"'),
                     ("# Qt is distributed as 'framework' on OS X; "
                      + "obviously we need this",
                       "    pass\n"),
                     ('for lib in qt_libraries:', '#\n'),
                     ("qimageview.extra_link_args.extend(['-framework', lib])",
                      '#\n'),
                     ('for d in qt_lib_dirs:', '#\n'),
                     ("qimageview.extra_link_args.append('-F' + d)", '#\n')
                    ]

    def configure_all(self):
        return ['python',
                'setup.py',
                'build',
                '&&',
                'python',
                'setup.py',
                'install'
               ]

    def configure_darwin(self):
        return ['--prefix="($prefix)/Frameworks/Python.framework/Versions/2.7"']

    def make(self):
        pass

    def makeInstall(self):
        pass

#===============================================================================
# GreenletPackage
#===============================================================================
class GreenletPackage(Package):
    src_file = 'greenlet.zip'

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
    src_file = 'blist.tar.gz'

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
    src_file = 'psutil.tar.gz'

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
    src_file = 'ipython.tar.gz'

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
    src_file = 'readline.tar.gz'

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
    src_file = 'vtk.tar.gz'

    replaceDarwin = ['Wrapping/Python/CMakeLists.txt',
                     ('SET(VTK_PYTHON_SETUP_ARGS',
                      '      SET(VTK_PYTHON_SETUP_ARGS --prefix='
                      + installDir
                      + '/Frameworks/Python.framework/Versions/2.7 \n')
                    ]

    def configure_all(self):
        return ['cmake . ',
                ####'-DVTK_PYTHON_SETUP_ARGS=--prefix=($prefix)',
                '-DSIP_EXECUTABLE:FILEPATH=($pythonBinaryPath)/sip',
                '-DSIP_INCLUDE_DIR:PATH=($pythonIncludePath)/sip',
                '-DSIP_PYQT_DIR:PATH=($pythonSharePath)/sip/PyQt4',
                '-DVTK_WRAP_PYTHON_SIP:BOOL=ON',
                '-DVTK_WRAP_PYTHON:BOOL=ON',
                '-DPYTHON_EXECUTABLE:FILEPATH=($pythonExecutable)',
                '-DPYTHON_INCLUDE_DIR:PATH=($pythonIncludePath)',
                '-DPYTHON_LIBRARY:FILEPATH=($pythonlib)',
                '-DCMAKE_SHARED_LIBS:BOOL=ON',
                '-DVTK_USE_QT:BOOL=ON',
                '-DVTK_USE_QVTK=ON',
                '-DVTK_USE_QVTK_QTOPENGL:BOOL=ON',
                '-DVTK_USE_QTOPENGL=ON',
                '-DVTK_WRAP_CPP=ON',
                '-DVTK_WRAP_UI=ON',
                '-DDESIRED_QT_VERSION=4',
                '-DCMAKE_INSTALL_PREFIX=($prefix)',
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
                '-DVTK_USE_SYSTEM_HDF5=ON',
                '-DVTK_USE_SYSTEM_EXPAT=ON', ###?
                '-DVTK_USE_SYSTEM_FREETYPE=OFF',
                '-DVTK_USE_SYSTEM_JPEG=ON',
                '-DVTK_USE_SYSTEM_LIBXML2=OFF',
                '-DVTK_USE_SYSTEM_PNG=ON',
                '-DVTK_USE_SYSTEM_TIFF=ON',
                '-DVTK_USE_SYSTEM_ZLIB=ON',
                '-DVTK_USE_HYBRID=ON',
                '-DVTK_USE_GL2PS=ON',
                '-DVTK_USE_RENDERING=ON',
                '-DVTK_USE_TK:BOOL=OFF',
                '-DJPEG_INCLUDE_DIR=($prefix)/include',
                '-DJPEG_LIBRARY=($prefix)/lib/libjpeg($dll_suffix)',
                '-DPNG_LIBRARY=($prefix)/lib/libpng($dll_suffix)',
                '-DPNG_PNG_INCLUDE_DIR=($prefix)/include',
                '-DTIFF_INCLUDE_DIR=($prefix)/include',
                '-DTIFF_LIBRARY=($prefix)/lib/libtiff($dll_suffix)',
                '-DZLIB_INCLUDE_DIR=($prefix)/include',
                '-DZLIB_LIBRARY=($prefix)/lib/libz($dll_suffix)',
                '-DHDF5_ROOT=($prefix)',
                '-DHDF5_INCLUDE_DIRS=($prefix)/include',
                '-DHDF5_INCLUDE_DIR=($prefix)/include',
                '-DHDF5_LIBRARIES=($prefix)/lib',
                '-DHDF5_LIBRARY=($prefix)/lib',
                ##'-DHDF5_INSTALL=($prefix)',
                ##'-DCMAKE_INSTALL_PREFIX=($prefix)',
                '../../work/($packageWorkDir)'
               ]

#===============================================================================
# LazyflowPackage
#===============================================================================
class LazyflowPackage(Package):
    src_file = 'lazyflow.tar'
    
    def configure_all(self):
        return ['cd .. && cp -r %s ($prefix)/%s' % (self.workdir, self.workdir),
                ' && cd ($prefix)/%s/lazyflow/drtile' % (self.workdir),
                ' && pwd',
                ' && cmake .',
                '-DPYTHON_EXECUTABLE=($pythonExecutable)',
                '-DBoost_INCLUDE_DIR=($prefix)/include',
                '-DBoost_PYTHON_LIBRARY_DEBUG=($prefix)/lib/'
                + 'libboost_python($dll_suffix)',
                '-DBoost_PYTHON_LIBRARY_RELEASE=($prefix)/lib/'
                + 'libboost_python($dll_suffix)',
                '-DPYTHON_INCLUDE_DIR=($pythonHeadersPath)',
                '-DPYTHON_LIBRARY=($pythonlib)',
                '-DVIGRA_IMPEX_LIBRARY=($prefix)/lib/'
                + 'libvigraimpex($dll_suffix)',
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
    src_file = 'volumina.tar'
    
    def configure_all(self):
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
    src_file = 'widgets.tar'
    
    def configure_all(self):
        return ['cd .. && cp -r %s ($prefix)/%s' % (self.workdir, self.workdir),
                ]
            
    def make(self):
        pass
    def makeInstall(self):
        pass

#===============================================================================
# AppletWorkflowsPackage
#===============================================================================
class AppletWorkflowsPackage(Package):
    src_file = 'applet-workflows.tar'
    
    def configure_all(self):
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
    def __init__(self, name):        
        self.package_name = name
        if platform.system() == "Linux":
            self.createFileLinux()
        if platform.system() == "Darwin":
            self.createFileDarwin()

    def createFileLinux(self):
        file_name = installDir + "/ilastik"
        file = open(file_name, "w")
        script_name = "ILASTIK_SCRIPT"
        script = "$" + script_name
        path_name = "ILASTIK_PATH"
        path = "$" + path_name
        print >>file, "#!/bin/bash"
        print >>file, script_name + "=$(readlink -f $0)"
        print >>file, path_name + "=$(dirname " + script + ")"
        print >>file, "export PATH=" + path + "/bin:$PATH"
        print >>file, ("export LD_LIBRARY_PATH=" + path + "/lib:" + path +
                       "/lib/python" + pythonVersion + "/site-packages/vigra")
        print >>file, ("export PYTHONPATH=" + path + "/volumina:" + path +
                       "/applet-workflows/ilastik-shell:" + path + "/widgets:" +
                       path + "/widgets/igms:" + path + "/lazyflow:" + path +
                       "/lazyflow/drtile:" + path + "/lib/python" +
                       pythonVersion + "/site-packages")
        print >>file, ("python" + pythonVersion + " " + path +
                       "/applet-workflows/ilastik-shell/workflows/" +
                       "pixelClassificationWorkflowMain.py")
        file.close()
        os.chmod(file_name, stat.S_IRUSR | stat.S_IXUSR | stat.S_IWUSR |
                            stat.S_IRGRP | stat.S_IXGRP |
                            stat.S_IROTH | stat.S_IXOTH)

    def createFileDarwin(self):
        file = open('%s/activate.sh' % (installDir), "w")
        file.write(("export PATH=%s/bin:%s/Frameworks/Python.framework/Versions"
                   + "/2.7/bin:$PATH\n") % (installDir, installDir))
        file.write(("export DYLD_FALLBACK_LIBRARY_PATH=%s/lib:%s/Frameworks/"
                   + "Python.framework/Versions/2.7/lib/python2.7/"
                   + "site-packages/vigra\n") % (installDir, installDir))
        file.write(("export PYTHONPATH=%s/volumina:%s/widgets:%s/lazyflow:%s/"
                   + "lazyflow/lazyflow/drtile:%s/Frameworks/Python.framework/"
                   + "Versions/2.7/lib/python2.7/site-packages\n") % (
                    installDir, installDir, installDir, installDir, installDir))
        file.write(("alias classificationWorkflow='python %s/techpreview/"
                   + "classification/classificationWorkflow.py'\n")
                   % (installDir))
        file.write("txtred='\e[0;31m' # Red\n")
        file.write("bldgrn='\e[1;32m' # Green\n")
        file.write("txtrst='\e[0m'    # Text Reset\n")
        file.write("print_before_the_prompt () {\n")
        file.write('    printf "\n $txtred%s: $bldgrn%s \n$txtrst" '
                   '"ilastik environment" "$PWD"\n')
        file.write("}\n")
        file.write("PROMPT_COMMAND=print_before_the_prompt\n")
        file.write("PS1='-> '")
        file.close()

