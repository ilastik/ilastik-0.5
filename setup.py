#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    Copyright 2010 C Sommer, C Straehle, U Koethe, FA Hamprecht. All rights reserved.
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

from distutils.core import setup
import py2exe

from glob import glob
    
msvs_redist = ("Microsoft.VC90.CRT", glob('./gui/msvs-redist/*.*'))

class Target:
    def __init__(self, **kw):
        self.__dict__.update(kw)

ilastikGUI = Target(
    name='IlastikGUI',
    version='0.3',
    company_name = "HCI",
    description='Interactive Learning and Segmentation Tool Kit- GUI',
    author='Christoph Sommer',
    author_email='christoph.sommer@iwr.uni-heidelberg.de',
    copyright = "",
    url='http://hci.iwr.uni-heidelberg.de/',
    script = "ilastikMain.py",
    icon_resources = [(1, "./gui/pyc.ico")]
)

setup(
    console = [ilastikGUI],
    data_files = [('gui', ['./gui/pyc.ico', "./gui/dlgChannels.ui", "./gui/dlgFeature.ui", "./gui/dlgProject.ui"]), msvs_redist],
    zipfile = "shared.lib",
    options = {"py2exe": {"compressed": 0, "optimize": 0, "includes":["sip", "core", "h5py", "h5py._stub", "numpy.matrixlib.defmatrix", "h5py.utils", "PyQt4.QtSvg", "labelArrayDrawQImage"], "dll_excludes": ["MSVCP90.dll", "MSVCR80.dll"]}},
)

print "*********************\n>>copy vigra numpy core"
import os
os.chdir('dist')
# os.system('copy vigra.vigranumpycore.pyd vigranumpycore.pyd' )
