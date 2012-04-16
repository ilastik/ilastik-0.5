#!/usr/bin/env python
# -*- coding: utf-8 -*-

import __builtin__
import platform
import urllib2, os, sys, tarfile, shutil
from hashlib import md5

c = sys.argv

#===============================================================================
# set install directory
#===============================================================================
for index, item in enumerate(c):
    if "prefix" in item:
        item = item.replace("--prefix=", "")
        __builtin__.installDir = item
        del c[index]
        break
    else:
        __builtin__.installDir = os.environ["HOME"]+"/ilastik-build"

import PackagesItems

#===============================================================================
# Create the initial structure of the project 
#===============================================================================
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

#===============================================================================
# set environment variables 
#===============================================================================
os.environ["PATH"]                       = installDir + "/bin:" + os.environ["PATH"] 
if '10.6' in platform.mac_ver()[0]:
	os.environ["MACOSX_DEPLOYMENT_TARGET"]   = "10.6"
elif '10.7' in platform.mac_ver()[0]:
	os.environ["MACOSX_DEPLOYMENT_TARGET"]   = "10.7"
os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = installDir + "/lib"
os.environ["CC"]                         = "llvm-gcc"
os.environ["CXX"]                        = "llvm-g++"
#no space between "-L" and directory path!!! It will causes a compiler error 
os.environ["LDFLAGS"]                    = "-L" + installDir + "/lib -F" + installDir + "/Frameworks"
os.environ["CPPFLAGS"]                   = "-I " + installDir + "/include"
os.environ["PYTHONPATH"]                 = installDir + "/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages"
os.environ["FRAMEWORK_PATH"]             = installDir + "/Frameworks"

#===============================================================================
# available packages
#===============================================================================
# first value is for the command line 
# second value is the method name in PackagesItems
# packages need to be in the right installation order 
all = [
    ('zlib', 'ZlibPackage'),                    ('slib', 'SlibPackage'),        ('python', 'PythonPackage'), 
    ('setuptools', 'SetuptoolsPackage'),              
    ('readline', 'ReadlinePackage'),            ('ipython', 'IpythonPackage'),
    ('fftw3', 'FFTW3Package'),                  ('fftw3f', 'FFTW3FPackage'),    ('jpeg', 'JpegPackage'), 
    ('tiff', 'TiffPackage'),                    ('png', 'PngPackage'),           
    ('nose', 'NosePackage'),                    ('hdf5', 'Hdf5Package'),        ('numpy', 'NumpyPackage'), 
    ('h5py', 'H5pyPackage'),                    ('boost', 'BoostPackage'),      ('vigra', 'VigraPackage'),
    ('qt', 'QtPackage'),                        ('sip', 'SipPackage'),          ('pyqt', 'PyQtPackage'), 
    ('qimage2ndarray', 'Qimage2ndarrayPackage'),('vtk', 'VTKPackage'),          ('greenlet', 'GreenletPackage'),
    ('blist', 'BlistPackage'),                  ('psutil', 'PsutilPackage'),	('lazyflow', 'LazyflowPackage'),
    ('volumina', 'VoluminaPackage'),			('widgets', 'WidgetsPackage'),	('techpreview', 'TechpreviewPackage'),
    ('envscript', 'EnvironmentScript'),
    #('test', 'Test'),
    #'fixes'
    ]
#===============================================================================
# create the package list for the installation
#===============================================================================
packages = []
for index, item in enumerate(c):
    if item == "all":
        packages = all
        break
    if item == "from":
        startpackage = c[index + 1]
        packageIndex = None
        for ind, itm in enumerate(all):
            if itm[0] == startpackage:
                packageIndex = ind
        if packageIndex:  
            packages = []
            for i in range(packageIndex,len(all)):
                packages.append(all[i])
                break
        else:
            print 'package: ', startpackage, ' not known'
if not packages:
    for item in all:
        for i in c:
            if i == item[0]:
                packages.append(item)
#===============================================================================
# install packages
#===============================================================================
for item in packages:
    package = getattr(PackagesItems, item[1])
    package()
	
         

