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

import traceback,  os,  sys
from ilastik.core.baseModuleMgr import BaseModuleMgr
#
#Import other segmentation plugins dynamically
#
try:
    if modules == None:
        pass
except:
    modules = []

def loadModuleCores():
    print "Loading modules core functionality..."

    pathext = os.path.dirname(__file__)
    abspath = os.path.abspath(pathext)
    for f in os.listdir(abspath):
        if os.path.isdir(abspath + "/" + f):
            module_name = f # Handles no-extension files, etc.
            try:
                module = __import__('ilastik.modules.' + module_name + '.core')
                print "Loaded core part of module" , module_name
            except Exception, e:
                traceback.print_exc(file=sys.stdout)
                pass
                    
    modules = BaseModuleMgr.__subclasses__()
    
    
    
def loadModuleGuis():
    print "Loading modules GUI functionality..."
    import ilastik.gui.ribbons.ilastikTabBase

    pathext = os.path.dirname(__file__)
    abspath = os.path.abspath(pathext)
    for f in os.listdir(abspath):
        if os.path.isdir(abspath + "/" + f):
            module_name = f # Handles no-extension files, etc.
            try:
                module = __import__('ilastik.modules.' + module_name + '.gui')
                print "Loaded GUI part of module " , module_name
            except Exception, e:
                traceback.print_exc(file=sys.stdout)
                pass
            
    print ilastik.gui.ribbons.ilastikTabBase.IlastikTabBase.__subclasses__()