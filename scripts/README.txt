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


#	The collection of scripts in this folderdownload and install all the dependencies required for
# 	the master branch of ilastik starting from version 0.56 .
#   These scripts have been tested on a clean machine running Mac Os X Snow Leopard 10.6.7
#	
#   
#	GETTING STARTED	(Mac Os X)
#
#	There are some basic ingredients needed: 
#	Install the Mac Os X Developers Enviroment with XCode from Mac Os X original Dvd
#	Install  CMake
#	Install  git
#
#	Create a folder called ilastik at the root of the computer and give to your user full rights to write into it. 
#   
#	sudo mkdir /ilastik
#   sudo chown yourusername /ilastik 


#	COMPILING 
# 	To install all the dependencies:
#	
#	python install-ilastik-deps.py all
#
#   To resume the installation process from a certain package:
#
#	python install-ilastik-deps.py from packagename
#
#	To install a certain package:
#  
#	python install-ilastik-deps.py packagename


# 	All the packages will be installed at:
#	~/ilastik_deps_build


#	RUN ILASTIK (Mac Os X)
#	execute ../run-ilastik-mac.sh

#   CREATE AN ILASTIK BOUNDLE (Mac Os X)
#	
#   execute ./make-osx-application-bundle.sh

