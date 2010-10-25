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
from setuptools import find_packages

import os

iconFileList = []
rootdir = 'ilastik/gui/icons/'
for root, subFolders, files in os.walk(rootdir):
    for file in files:
        iconFileList.append(os.path.join(root[12:],file))

uiFileList  = []
rootdir = 'ilastik/gui/'
for root, subFolders, files in os.walk(rootdir):
    for file in files:
        if '.ui' in file:
            uiFileList.append(os.path.join(root[12:],file))
        
iconFileList.extend(uiFileList)

setup(name = 'ilastik',
      version = '0.5',
      description = 'Interactive Learning and Segmentation Tool Kit',
      author = 'Christoph Sommer, Christoph Straehle, Ullrich Koethe, Fred A. Hamprecht',
      author_email = 'ilastik@hci.iwr.uni-heidelberg.de',
      url = 'http://www.ilastik.org',
      download_url = 'http://www.ilastik.org',
      keywords = ['segmentation', 'numpy', 'ndarray', 'image', 'classification', 'PyQt4'],
      packages = find_packages(),
      py_modules = ['ilastik/ilastikMain'],
      package_data = {'ilastik.gui' : iconFileList},
      long_description = ''' ''')